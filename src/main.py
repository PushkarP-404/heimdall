from src.sheets import GoogleSheetsManager
from src.github import GitHubManager
from src.llm import LLMAnalyzer
from src.discord import DiscordNotifier

def main():
    print("Starting Heimdall Issue Finder Agent (Phase 4)...")

    # Initialize Managers
    sheets_manager = GoogleSheetsManager()
    github_manager = GitHubManager()
    llm_analyzer = LLMAnalyzer(github_manager.headers)
    discord_notifier = DiscordNotifier()

    # Step 1: Get existing issues to prevent duplicates
    existing_urls = sheets_manager.get_existing_issue_urls()
    print(f"Found {len(existing_urls)} existing issues in the Google Sheet.")

    # Step 2: Search GitHub for new issues
    raw_new_issues = github_manager.search_issues(existing_urls)
    
    if not raw_new_issues:
        print("No new raw issues found.")
        return

    print(f"Discovered {len(raw_new_issues)} new raw issues. Passing to LLM for intelligence filtering...")
    
    # Step 3: Filter with LLM and Priority Checks
    filtered_issues = []
    for issue in raw_new_issues:
        repo_url = issue['repository_url']
        
        # Check 1: Repo Analysis (Welcoming + GSoC)
        repo_analysis = llm_analyzer.analyze_repo(repo_url)
        if not repo_analysis["is_welcoming"]:
            print(f"  [Skip] Repo not welcoming: {issue['html_url']}")
            continue
            
        # Check 2: Issue Analysis (Actionable + Effort)
        issue_analysis = llm_analyzer.analyze_issue(issue['title'], issue.get('body', ''))
        if not issue_analysis["is_actionable"]:
            print(f"  [Skip] Issue not actionable: {issue['html_url']}")
            continue
            
        # Check 3: Stars (Optional, for priority)
        repo_details = github_manager.get_repo_details(repo_url)
        stars = repo_details.get("stargazers_count", 0)
        
        # Determine Priority
        # We consider it high priority if it has lots of stars (> 500) or requires high effort
        is_high_priority = (stars >= 500) or (issue_analysis["effort"] == "HIGH")
        is_gsoc = repo_analysis["is_gsoc"]
        
        issue["_is_high_priority"] = is_high_priority
        issue["_is_gsoc"] = is_gsoc

        # Passed all checks!
        print(f"  [Keep] High quality issue found: {issue['html_url']} (Priority: {is_high_priority}, GSoC: {is_gsoc})")
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
            import time
            time.sleep(1) # Prevent Discord rate limits
    else:
        print("No issues passed the LLM filter.")

if __name__ == "__main__":
    main()
