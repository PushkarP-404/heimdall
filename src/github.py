import time
from datetime import datetime, timezone, timedelta
import requests
from src.config import (
    PAT_TOKEN,
    CURATED_BEGINNER_TAGS,
    BROAD_TAGS,
    MIN_STARS,
    MIN_STARS_BROAD,
    MAX_COMMENTS,
    MIN_BODY_LENGTH,
    EXCLUDE_LABELS,
    TARGET_LANGUAGES,
)


class GitHubManager:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if PAT_TOKEN:
            self.headers["Authorization"] = f"token {PAT_TOKEN}"
        self.repo_details_cache = {}

    def _execute_search(self, query, per_page=10):
        """Execute a GitHub issue search with rate-limit handling and backoff."""
        base_url = "https://api.github.com/search/issues"
        params = {
            "q": query,
            "sort": "created",
            "order": "desc",
            "per_page": per_page,
        }

        for attempt in range(2):
            try:
                response = requests.get(base_url, headers=self.headers, params=params, timeout=20)
                if response.status_code == 200:
                    return response.json().get("items", [])
                elif response.status_code in (403, 429):
                    # Check for rate limit or secondary rate limit
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        wait_sec = int(retry_after) + 2
                        print(f"  [GitHub API] Rate limit hit. Waiting {wait_sec}s (Retry-After)...")
                        time.sleep(wait_sec)
                    elif response.headers.get("x-ratelimit-remaining") == "0":
                        print("  [GitHub API] Primary search rate limit reached for this window.")
                        return []
                    else:
                        print("  [GitHub API] Secondary rate limit encountered. Pacing request...")
                        time.sleep(15)
                else:
                    print(f"  [GitHub API] Search error ({response.status_code}): {response.text[:150]}")
                    return []
            except Exception as e:
                print(f"  [GitHub API] Request exception: {e}")
                return []

        return []

    def search_issues(self, existing_urls):
        """
        Multi-tier search:
        1. Curated beginner tags with standard star threshold and comment ceiling.
        2. Broad tags (bug, enhancement) with strict high-star threshold.
        3. Optional language qualifiers if TARGET_LANGUAGES configured.
        """
        found_issues = []
        seen_urls = set(existing_urls)

        # Build search strategies: (tag, min_stars, max_comments)
        search_plans = []

        for tag in CURATED_BEGINNER_TAGS:
            search_plans.append({"tag": tag, "min_stars": MIN_STARS, "max_comments": MAX_COMMENTS})

        for tag in BROAD_TAGS:
            search_plans.append({"tag": tag, "min_stars": MIN_STARS_BROAD, "max_comments": 3})

        for plan in search_plans:
            tag = plan["tag"]
            min_stars = plan["min_stars"]
            max_comments = plan["max_comments"]

            # Base query
            query = (
                f'is:open is:issue no:assignee archived:false locked:false '
                f'comments:<={max_comments} stars:>={min_stars} label:"{tag}"'
            )

            # If user configured specific target languages, append or search by language
            if TARGET_LANGUAGES:
                for lang in TARGET_LANGUAGES:
                    lang_query = f"{query} language:{lang}"
                    print(f"Searching GitHub for [{tag}] in [{lang}] (stars>={min_stars})...")
                    items = self._execute_search(lang_query, per_page=10)
                    for item in items:
                        url = item.get("html_url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            found_issues.append(item)
                    time.sleep(4)
            else:
                print(f"Searching GitHub for [{tag}] (stars>={min_stars}, comments<={max_comments})...")
                items = self._execute_search(query, per_page=10)
                for item in items:
                    url = item.get("html_url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        found_issues.append(item)
                # Respect secondary search rate limits
                time.sleep(4)

        return found_issues

    def get_repo_details(self, repo_api_url):
        """Fetch repository details with in-memory caching."""
        if not repo_api_url:
            return {}
        if repo_api_url in self.repo_details_cache:
            return self.repo_details_cache[repo_api_url]

        try:
            response = requests.get(repo_api_url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                self.repo_details_cache[repo_api_url] = data
                return data
            else:
                print(f"  [GitHub API] Repo details error ({response.status_code}) for {repo_api_url}")
        except Exception as e:
            print(f"  [GitHub API] Failed fetching repo details: {e}")

        return {}

    def is_repo_active_and_healthy(self, repo_details, min_stars=MIN_STARS):
        """
        Deterministic health check on repository before invoking LLM:
        - Must not be archived or disabled
        - Must have minimum stars (unless GSoC exempt)
        - Must have had a commit/push in the last 2 years (not an abandoned repository)
        """
        if not repo_details:
            return False, "Could not fetch repo details"

        if repo_details.get("archived", False):
            return False, "Repository is archived"

        if repo_details.get("disabled", False):
            return False, "Repository is disabled"

        stars = repo_details.get("stargazers_count", 0)
        if stars < min_stars:
            return False, f"Stars ({stars}) below minimum ({min_stars})"

        pushed_at_str = repo_details.get("pushed_at")
        if pushed_at_str:
            try:
                pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
                two_years_ago = datetime.now(timezone.utc) - timedelta(days=730)
                if pushed_at < two_years_ago:
                    return False, f"Repository inactive since {pushed_at_str[:10]}"
            except Exception:
                pass

        return True, "Healthy"

    def is_issue_prequalified(self, issue):
        """
        Fast filter on issue itself:
        - Must not be a Pull Request
        - Must have a non-trivial body description
        - Must not have excluded labels (wontfix, duplicate, etc.)
        - Must not exceed comment limit
        """
        if "pull_request" in issue:
            return False, "Item is a pull request, not an issue"

        body = (issue.get("body") or "").strip()
        if len(body) < MIN_BODY_LENGTH:
            return False, f"Issue body too short ({len(body)} chars)"

        labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
        for l in labels:
            if l in EXCLUDE_LABELS:
                return False, f"Issue contains excluded label '{l}'"

        comments = issue.get("comments", 0)
        if comments > MAX_COMMENTS:
            return False, f"Too many comments ({comments} > {MAX_COMMENTS})"

        return True, "Prequalified"
