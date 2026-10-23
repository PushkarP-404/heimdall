import requests
from datetime import datetime, timezone
from src.config import DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_URL_HIGH_PRIORITY


class DiscordNotifier:
    def send_notification(self, issue, is_high_priority=False, is_gsoc=False):
        if is_high_priority and DISCORD_WEBHOOK_URL_HIGH_PRIORITY:
            webhook_url = DISCORD_WEBHOOK_URL_HIGH_PRIORITY
            print(f"  [Discord] Routing to HIGH PRIORITY channel: {issue['html_url']}")
        elif DISCORD_WEBHOOK_URL:
            webhook_url = DISCORD_WEBHOOK_URL
            if is_high_priority:
                print(f"  [Discord] Warning: HP webhook not set — falling back to standard channel: {issue['html_url']}")
            else:
                print(f"  [Discord] Routing to standard channel: {issue['html_url']}")
        else:
            print("  [Discord] No webhook URLs configured, skipping notification.")
            return

        analysis = issue.get("_analysis", {})
        stars = issue.get("_stars", 0)
        language = issue.get("_language", "Unknown")
        difficulty = analysis.get("difficulty", "Good First Issue")
        effort = analysis.get("estimated_effort", "Quick Fix (<2h)")
        quality_score = analysis.get("quality_score", 7)
        summary = analysis.get("summary") or issue.get("title", "")
        skills = ", ".join(analysis.get("recommended_skills", [])) or language
        comments = issue.get("comments", 0)

        # Dynamic Badge Prefix
        badges = []
        if is_gsoc:
            badges.append("🏛️ [GSoC]")
        if is_high_priority:
            badges.append("⭐ [HIGH PRIORITY]")
        elif difficulty == "Good First Issue":
            badges.append("🌱 [GOOD FIRST ISSUE]")

        title_prefix = " ".join(badges) + " " if badges else "🎯 [NEW MATCH] "

        # Dynamic Color Palette
        if is_gsoc:
            color = 16096779  # Gold / Amber
        elif is_high_priority:
            color = 9133302   # Violet / Purple
        elif difficulty == "Good First Issue":
            color = 1096065   # Emerald Green
        else:
            color = 3900150   # Blue

        labels = ", ".join([l["name"] for l in issue.get("labels", [])][:5])
        repo_name = issue["repository_url"].split("repos/")[-1]
        repo_html_url = f"https://github.com/{repo_name}"

        # Format comment/competition status
        if comments == 0:
            comment_status = "0 comments (Unclaimed)"
        else:
            comment_status = f"{comments} comments"

        # Build Rich Discord Embed
        embed = {
            "title": f"{title_prefix}{issue['title']}"[:256],
            "url": issue["html_url"],
            "description": f"**AI Action Summary:**\n{summary}",
            "color": color,
            "fields": [
                {
                    "name": "📁 Repository",
                    "value": f"[{repo_name}]({repo_html_url}) (⭐ {stars:,})",
                    "inline": True,
                },
                {
                    "name": "💻 Language",
                    "value": language if language else "Not specified",
                    "inline": True,
                },
                {
                    "name": "🎯 Difficulty",
                    "value": difficulty,
                    "inline": True,
                },
                {
                    "name": "⏱️ Effort",
                    "value": effort,
                    "inline": True,
                },
                {
                    "name": "⚡ Quality Rating",
                    "value": f"{quality_score} / 10",
                    "inline": True,
                },
                {
                    "name": "💬 Discussion",
                    "value": comment_status,
                    "inline": True,
                },
                {
                    "name": "🛠️ Recommended Skills",
                    "value": skills if skills else "General",
                    "inline": False,
                },
                {
                    "name": "🏷️ Labels",
                    "value": labels if labels else "None",
                    "inline": False,
                },
            ],
            "footer": {
                "text": "Heimdall Issue Intelligence • Autonomous Discovery"
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        data = {
            "content": "👁️‍🗨️ **Heimdall** identified a verified, high-quality open source issue!",
            "embeds": [embed],
        }

        try:
            response = requests.post(webhook_url, json=data, timeout=15)
            if response.status_code not in (200, 204):
                print(f"Discord Webhook Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")
