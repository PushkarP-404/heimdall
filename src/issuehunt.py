import json
import time
import requests
from google import genai
from playwright.sync_api import sync_playwright
from src.config import GEMINI_API_KEY, DISCORD_WEBHOOK_URL_ISSUEHUNT, ISSUEHUNT_SESSION_TOKEN
from src.sheets import GoogleSheetsManager

DISCORD_WEBHOOK = DISCORD_WEBHOOK_URL_ISSUEHUNT
SESSION_TOKEN = ISSUEHUNT_SESSION_TOKEN


def send_discord_notification(bounty):
    if not DISCORD_WEBHOOK:
        return

    embed = {
        "title": f"💰 Bounty: {bounty.get('title', 'Unknown')}",
        "url": bounty.get("url", "https://issuehunt.io"),
        "description": "New bounty discovered on IssueHunt!",
        "color": 16766720,  # Gold
        "fields": [
            {"name": "Amount", "value": bounty.get("amount", "Unknown"), "inline": True}
        ],
    }
    requests.post(DISCORD_WEBHOOK, json={"content": "New Bounty!", "embeds": [embed]})


def scrape_bounties():
    print("Starting IssueHunt scraper...")

    # Load existing seen bounties for deduplication
    sheets_manager = GoogleSheetsManager()
    existing_urls = sheets_manager.get_existing_bounty_urls()
    print(f"  [Sheets] {len(existing_urls)} previously seen bounties loaded.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # If user provided a session cookie, inject it
        if SESSION_TOKEN:
            try:
                # Expecting a JSON array of cookies
                cookies = json.loads(SESSION_TOKEN)
                context.add_cookies(cookies)
                print("Injected session cookies.")
            except Exception:
                print("Warning: ISSUEHUNT_SESSION_TOKEN is not valid JSON. Ignoring.")

        page = context.new_page()
        page.goto("https://issuehunt.io/issues", wait_until="networkidle")

        # Wait for any CSR (Client-Side Rendering) to finish
        page.wait_for_timeout(5000)

        # Extract all links and their text context
        links_data = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim() || a.textContent.trim(),
                url: a.href
            })).filter(a => a.url && a.text);
        }""")

        browser.close()

    print(f"Extracted {len(links_data)} links from the page. Sending to LLM for parsing...")

    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY missing. Cannot parse bounties.")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    You are an AI data extractor. I scraped all the links from IssueHunt.io.
    Your job is to identify the open bounties or issues from this list.
    Return ONLY a raw JSON array of objects (no markdown blocks, no backticks).
    Each object must have exactly 3 keys: "title", "url", "amount".
    If no amount is found, use "Check Link".
    Ignore generic links like "Log in", "Home", "Terms", etc.
    
    Links data:
    {json.dumps(links_data)[:30000]}
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )

        # Clean up Markdown backticks if the LLM includes them
        raw_json = response.text.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.startswith("```"):
            raw_json = raw_json[3:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]

        all_bounties = json.loads(raw_json.strip())
        print(f"LLM identified {len(all_bounties)} bounties total.")

        # ── Deduplication ────────────────────────────────────────────────────
        new_bounties = [b for b in all_bounties if b.get("url") not in existing_urls]
        skipped = len(all_bounties) - len(new_bounties)
        print(f"  {len(new_bounties)} new bounties after deduplication ({skipped} already seen, skipped).")

        for bounty in new_bounties:
            send_discord_notification(bounty)
            time.sleep(1)  # Prevent Discord rate limits

        # Persist new bounties so future runs skip them
        sheets_manager.append_bounties(new_bounties)

    except Exception as e:
        print(f"Error parsing or sending bounties: {e}")


if __name__ == "__main__":
    scrape_bounties()
