import requests
from src.config import DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_URL_HIGH_PRIORITY

class DiscordNotifier:
    def send_notification(self, issue, is_high_priority=False, is_gsoc=False):
        if is_high_priority and DISCORD_WEBHOOK_URL_HIGH_PRIORITY:
            webhook_url = DISCORD_WEBHOOK_URL_HIGH_PRIORITY
            print(f"  [Discord] Routing to HIGH PRIORITY channel: {issue['html_url']}")
        elif DISCORD_WEBHOOK_URL:
            webhook_url = DISCORD_WEBHOOK_URL
            if is_high_priority:
                print(f"  [Discord] WARNING: HP webhook not set — falling back to normal channel for: {issue['html_url']}")
            else:
                print(f"  [Discord] Routing to normal channel: {issue['html_url']}")
        else:
            print("  [Discord] No webhook URLs configured, skipping notification.")
            return
            
        labels = ", ".join([l['name'] for l in issue.get('labels', [])])
        
        title_prefix = "⭐ [HIGH PRIORITY] " if is_high_priority else "New Match: "
        if is_gsoc:
            title_prefix = "🚀 [GSoC ORG] " + title_prefix
            
        embed = {
            "title": f"{title_prefix}{issue['title']}",
            "url": issue['html_url'],
            "description": issue.get('body', '')[:200] + "..." if issue.get('body') else "No description provided.",
            "color": 15158332 if is_high_priority else 3447003, # Red for high priority, Blue for normal
            "fields": [
                {"name": "Repository", "value": issue['repository_url'].split('repos/')[-1], "inline": True},
                {"name": "Labels", "value": labels if labels else "None", "inline": True},
                {"name": "Priority", "value": "High 🔴" if is_high_priority else "Normal 🔵", "inline": True}
            ]
        }
        
        data = {
            "content": "Heimdall found a high-quality issue for you to check out! :eyes:",
            "embeds": [embed]
        }
        
        try:
            response = requests.post(webhook_url, json=data)
            if response.status_code not in (200, 204):
                print(f"Discord Webhook Error: {response.status_code}")
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")
