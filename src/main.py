import time
from src.sheets import GoogleSheetsManager
from src.github import GitHubManager
from src.llm import LLMAnalyzer
from src.discord import DiscordNotifier
from src.gsoc import get_gsoc_github_orgs, is_gsoc_org

def main():
    print("Starting Heimdall Issue Finder Agent (Phase 4)...")

    # Initialize Managers
    sheets_manager = GoogleSheetsManager()
    github_manager = GitHubManager()
    llm_analyzer = LLMAnalyzer(github_manager.headers)
    discord_notifier = DiscordNotifier()

    # Step 1: Pre-load the verified GSoC org list (fetched once, cached in-process)
    get_gsoc_github_orgs()

    # Step 2: Get existing issues to prevent duplicates
    existing_urls = sheets_manager.get_existing_issue_urls()
    print(f"Found {len(existing_urls)} existing issues in the Google Sheet.")

    # Step 3: Search GitHub for new issues
    raw_new_issues = github_manager.search_issues(existing_urls)
    
    if not raw_new_issues:
        print("No new raw issues found.")
        return

    print(f"Discovered {len(raw_new_issues)} new raw issues. Passing to LLM for intelligence filtering...")
    
    # Step 4: Filter with LLM and Priority Checks
    filtered_issues = []
    for issue in raw_new_issues:
        repo_url = issue['repository_url']

        # Check 1: Verified GSoC org lookup (deterministic — no LLM needed)
        is_gsoc = is_gsoc_org(repo_url)

        # Check 2: Repo Analysis (Welcoming)
        repo_analysis = llm_analyzer.analyze_repo(repo_url)
        if not repo_analysis["is_welcoming"]:
            print(f"  [Skip] Repo not welcoming: {issue['html_url']}")
            continue

        # Check 3: Issue Analysis (Actionable + Effort)
        issue_analysis = llm_analyzer.analyze_issue(issue['title'], issue.get('body', ''))
        if not issue_analysis["is_actionable"]:
            print(f"  [Skip] Issue not actionable: {issue['html_url']}")
            continue

        # Check 4: Stars (for priority signal)
        repo_details = github_manager.get_repo_details(repo_url)
        stars = repo_details.get("stargazers_count", 0)

        # Determine Priority
        # High priority = is a GSoC org OR repo is very popular (>= 1000 stars).
        # Using OR instead of AND so either signal alone is enough.
        # Effort == "HIGH" is intentionally excluded — high effort = hard for newcomers.
        is_high_priority = is_gsoc or (stars >= 1000)

        issue["_is_high_priority"] = is_high_priority
        issue["_is_gsoc"] = is_gsoc

        # Passed all checks!
        print(f"  [Keep] High quality issue found: {issue['html_url']} (Priority: {is_high_priority}, GSoC: {is_gsoc}, Stars: {stars})")
        filtered_issues.append(issue)

    if filtered_issues:

        print(f"\nAfter LLM filtering, {len(filtered_issues)} high-quality issues remain.")
        # Step 4: Append to Google Sheets
        sheets_manager.append_issues(filtered_issues)
        
        # Step 5: Send Discord Notifications
        print("Sending Discord notifications...")
        for issue in filtered_issues:
            discord_notifier.send_notification(
                issue,
                is_high_priority=issue.get("_is_high_priority", False),
                is_gsoc=issue.get("_is_gsoc", False)
            )
            time.sleep(1)  # Prevent Discord rate limits
    else:
        print("No issues passed the LLM filter.")

if __name__ == "__main__":
    main()
