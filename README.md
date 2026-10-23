# Heimdall Issue Finder 👁️‍🗨️

Heimdall is an autonomous AI agent that runs on a schedule to discover, filter, and track high-quality open source issues on GitHub.

## Features

- **Multi-Tier Intelligent Discovery**: Categorizes searches across curated beginner tags (`good first issue`, `help wanted`, `first-timers-only`, `up-for-grabs`) and high-impact popular repositories (`stars:>=300`).
- **Deterministic Quality Gating**: Automatically filters out archived repositories, disabled projects, dead repos without recent commits, pull requests, and crowded issues (`comments > MAX_COMMENTS`) before making LLM calls.
- **Deep LLM Intelligence (Gemini)**: Evaluates documentation friendliness (`README.md` / `CONTRIBUTING.md`), rates issue actionability, estimates difficulty and effort, generates a 1-sentence TL;DR summary, identifies required skills, and assigns a 1–10 quality score.
- **Priority & GSoC Tracking**: Identifies high-effort issues, highly-starred repositories (>1,000 stars), and organizations participating in Google Summer of Code (GSoC) — combining live API data with curated open-source umbrella foundations (PSF, Apache, Mozilla, Wikimedia, etc.).
- **Enriched Google Sheets Integration**: Logs discovered issues with full metadata (Stars, Language, Difficulty, Effort, Status, and AI Summary) while preserving 100% backwards compatibility.
- **Rich Discord Alerts**: Dispatches color-coded, badge-tagged notifications displaying repository stars, primary language, difficulty pills, recommended skills, and AI summaries.
- **Manual Claiming Workflow**: Trigger a GitHub Action to let Gemini draft and post a professional, context-aware claim comment directly to GitHub.
- **IssueHunt Bounty Web Scraper**: Scrapes open bounties from IssueHunt and routes them to a dedicated Discord channel and Google Sheet.

## Configuration & Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PAT_TOKEN` | Required | GitHub Personal Access Token (with `repo` & `workflow` scopes) |
| `GEMINI_API_KEY` | Required | Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model name for intelligence and parsing |
| `GOOGLE_SHEET_ID` | Required | Google Sheets Spreadsheet ID |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `service_account.json` | Path or raw JSON string for Google Service Account |
| `DISCORD_WEBHOOK_URL` | Optional | Standard Discord webhook notification channel |
| `DISCORD_WEBHOOK_URL_HIGH_PRIORITY` | Optional | Webhook for High-Priority / GSoC issues |
| `DISCORD_WEBHOOK_URL_ISSUEHUNT` | Optional | Webhook for IssueHunt bounties |
| `MIN_STARS` | `30` | Minimum repository stars for curated beginner issues |
| `MIN_STARS_BROAD` | `300` | Minimum stars for broad labels (`bug`, `enhancement`) |
| `HIGH_PRIORITY_STARS` | `1000` | Threshold to flag repository as high-priority |
| `MAX_COMMENTS` | `5` | Maximum comments allowed on an issue to avoid already-claimed tasks |
| `MIN_QUALITY_SCORE` | `6` | Minimum LLM quality score (1–10) required to keep an issue |
| `TARGET_LANGUAGES` | None (all) | Comma-separated list to filter by language (e.g. `python,typescript,go`) |

## Setup & Deployment

Heimdall runs entirely for free using GitHub Actions and requires zero maintenance. To deploy your own instance:
1. Fork or clone this repository.
2. Go to your repository **Settings** -> **Secrets and variables** -> **Actions**.
3. Add the required Repository Secrets listed above.
4. The Heimdall cron jobs will automatically begin running every hour!

