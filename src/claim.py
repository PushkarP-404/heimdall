import os
import requests
from google import genai
from src.config import PAT_TOKEN, GEMINI_API_KEY
from src.sheets import GoogleSheetsManager

ISSUE_URL = os.getenv("ISSUE_URL")

def main():
    if not ISSUE_URL:
        print("Error: ISSUE_URL is not set.")
        return
        
    print(f"Starting manual claim workflow for: {ISSUE_URL}")
    
    # Parse URL
    parts = ISSUE_URL.replace("https://github.com/", "").split("/")
    if len(parts) < 4:
        print("Error: Invalid GitHub Issue URL.")
        return
        
    owner, repo, _, issue_number = parts[:4]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {PAT_TOKEN}"
    }

    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching issue details: {response.status_code}")
        return
        
    issue_data = response.json()
    
    # Draft comment with Gemini
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found.")
        return
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
    You are an open source contributor. You want to claim this issue.
    Draft a short, polite comment (1-2 sentences) asking to be assigned.
    Do not be overly formal. Just ask if you can take a look or work on it.
    Issue Title: {issue_data['title']}
    Issue Body: {str(issue_data.get('body', ''))[:1000]}
    """
    
    try:
        print("Drafting comment with Gemini...")
        llm_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        comment_text = llm_response.text.strip()
    except Exception as e:
        print(f"Error generating comment: {e}")
        return
        
    print(f"\nDrafted Comment:\n{comment_text}\n")
    
    # Post comment
    print("Posting comment to GitHub...")
    comment_url = issue_data['comments_url']
    post_resp = requests.post(comment_url, headers=headers, json={"body": comment_text})
    
    if post_resp.status_code == 201:
        print("Successfully posted comment!")
        
        # Update Google Sheet
        print("Updating Google Sheet status to 'Claimed'...")
        sheets_manager = GoogleSheetsManager()
        sheets_manager.update_issue_status(ISSUE_URL, "Claimed")
        print("Done!")
    else:
        print(f"Failed to post comment: {post_resp.text}")

if __name__ == "__main__":
    main()
