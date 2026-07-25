import requests
from src.config import PAT_TOKEN, SEARCH_TAGS
import urllib.parse

class GitHubManager:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if PAT_TOKEN:
            self.headers["Authorization"] = f"token {PAT_TOKEN}"

    def search_issues(self, existing_urls):
        found_issues = []
        base_url = "https://api.github.com/search/issues"

        # Search for each tag separately since we can't OR labels in GitHub search easily
        for tag in SEARCH_TAGS:
            # Query: open issues, no assignee, specific label
            query = f'state:open type:issue no:assignee label:"{tag}"'
            
            params = {
                "q": query,
                "sort": "created",
                "order": "desc",
                "per_page": 10  # Limit to top 10 most recent per tag to save rate limits
            }

            print(f"Searching GitHub for: {tag}...")
            response = requests.get(base_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    if item["html_url"] not in existing_urls:
                        # Avoid adding duplicates across different tag searches
                        if item["html_url"] not in [i["html_url"] for i in found_issues]:
                            found_issues.append(item)
            else:
                print(f"Failed to search for tag {tag}: {response.status_code} - {response.text}")

            # Sleep for 5 seconds to avoid GitHub Search API secondary rate limits
            import time
            time.sleep(5)

        return found_issues

    def get_repo_details(self, repo_api_url):
        response = requests.get(repo_api_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return {}
