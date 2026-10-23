import time
from src.config import MIN_STARS, HIGH_PRIORITY_STARS, MIN_QUALITY_SCORE
from src.sheets import GoogleSheetsManager
from src.github import GitHubManager
from src.llm import LLMAnalyzer
from src.discord import DiscordNotifier
from src.gsoc import get_gsoc_github_orgs, is_gsoc_org


def main():
    print("Starting Heimdall Issue Finder Agent (Upgraded Intelligence Phase)...")

    # Initialize Managers
    sheets_manager = GoogleSheetsManager()
    github_manager = GitHubManager()
    llm_analyzer = LLMAnalyzer(github_manager.headers)
    discord_notifier = DiscordNotifier()

    # Step 1: Pre-load GSoC organizations list (cached in-process)
    get_gsoc_github_orgs()

    # Step 2: Get existing issues to prevent duplicates
    existing_urls = sheets_manager.get_existing_issue_urls()
    print(f"Found {len(existing_urls)} existing issues in the Google Sheet.")

    # Step 3: Search GitHub using intelligent multi-tier discovery
    raw_new_issues = github_manager.search_issues(existing_urls)

    if not raw_new_issues:
        print("No new raw issues discovered in this run.")
        return

    print(f"\nDiscovered {len(raw_new_issues)} raw candidates. Running multi-tier intelligence pipeline...\n")

    # Step 4: Filtering Pipeline (Deterministic Gates first, LLM second)
    filtered_issues = []
    for issue in raw_new_issues:
        issue_url = issue["html_url"]
        repo_url = issue["repository_url"]
        repo_name = repo_url.split("repos/")[-1]

        # Gate 1: Fast issue prequalification (body length, excluded labels, comments)
        prequal, reason = github_manager.is_issue_prequalified(issue)
        if not prequal:
            print(f"  [Skip Issue] {reason}: {issue_url}")
            continue

        # Gate 2: Fast repository health check (archived, stars, recent commit activity)
        repo_details = github_manager.get_repo_details(repo_url)
        is_gsoc = is_gsoc_org(repo_url)

        # GSoC orgs are granted a lower star threshold since their mentorship makes them valuable
        effective_min_stars = 10 if is_gsoc else MIN_STARS
        active, reason = github_manager.is_repo_active_and_healthy(repo_details, min_stars=effective_min_stars)
        if not active:
            print(f"  [Skip Repo] {reason} ({repo_name}): {issue_url}")
            continue

        # Gate 3: Repository Welcoming check via LLM
        repo_analysis = llm_analyzer.analyze_repo(repo_url)
        if not repo_analysis["is_welcoming"]:
            print(f"  [Skip Repo] Documentation does not welcome contributors: {issue_url}")
            continue

        # Gate 4: Deep Issue Viability & Quality Evaluation via LLM
        stars = repo_details.get("stargazers_count", 0)
        language = repo_details.get("language") or "General"
        issue_analysis = llm_analyzer.analyze_issue(
            issue_title=issue["title"],
            issue_body=issue.get("body", ""),
            repo_name=repo_name,
            language=language,
        )

        if not issue_analysis["is_actionable"]:
            print(f"  [Skip Issue] Not actionable ({issue_analysis.get('verdict_reason')}): {issue_url}")
            continue

        quality_score = issue_analysis.get("quality_score", 7)
        if quality_score < MIN_QUALITY_SCORE:
            print(f"  [Skip Issue] Quality score {quality_score} below minimum {MIN_QUALITY_SCORE}: {issue_url}")
            continue

        # Determine Priority: GSoC organization OR high popularity repo
        is_high_priority = is_gsoc or (stars >= HIGH_PRIORITY_STARS)

        # Attach enriched metadata to issue
        issue["_is_high_priority"] = is_high_priority
        issue["_is_gsoc"] = is_gsoc
        issue["_stars"] = stars
        issue["_language"] = language
        issue["_analysis"] = issue_analysis

        print(
            f"  [Keep] High quality issue: {issue_url} | "
            f"Difficulty: {issue_analysis.get('difficulty')} | "
            f"Stars: {stars:,} | Score: {quality_score}/10 | "
            f"GSoC: {is_gsoc}"
        )
        filtered_issues.append(issue)

    # Step 5: Save to Google Sheets and Send Discord Notifications
    if filtered_issues:
        print(f"\nPipeline complete: {len(filtered_issues)} verified high-quality issues selected.")
        sheets_manager.append_issues(filtered_issues)

        print("Dispatching rich Discord alerts...")
        for issue in filtered_issues:
            discord_notifier.send_notification(
                issue,
                is_high_priority=issue.get("_is_high_priority", False),
                is_gsoc=issue.get("_is_gsoc", False),
            )
            time.sleep(1)  # Prevent Discord webhook rate limits
    else:
        print("\nPipeline complete: No raw issues met the quality standards in this cycle.")


if __name__ == "__main__":
    main()
