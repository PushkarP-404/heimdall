# Heimdall Issue Finder 👁️‍🗨️

Heimdall is an autonomous AI agent that runs on a schedule to discover, filter, and track high-quality open source issues on GitHub.

## Features

- **Automated Discovery**: Searches GitHub for issues using specific tags (e.g., `good first issue`, `help wanted`, `bug`).
- **LLM Intelligence**: Uses the Gemini API to analyze the repository's `README.md` and `CONTRIBUTING.md` to ensure they actively welcome external contributors, and evaluates the issue description to ensure it's actionable.
- **Priority & GSoC Tracking**: Identifies high-effort issues, highly-starred repositories (>500 stars), and organizations participating in Google Summer of Code (GSoC).
- **Google Sheets Integration**: Logs discovered issues to a Google Sheet to prevent duplicates and track status.
- **Discord Alerts**: Sends rich, color-coded alerts to Discord when matches are found.
- **Manual Claiming Workflow**: Trigger a GitHub Action to let the LLM draft and politely post a professional, context-aware claim comment on the issue.
- **IssueHunt Web Scraper**: Runs a headless Chromium browser to scrape open bounties from IssueHunt's dynamic website and sends them directly to a dedicated Discord channel using Gemini LLM

## Community

We track and route these issues dynamically.
👉 **[Join our Discord Channel Here (https://discord.gg/TfpjARhMn)](#)**

## Setup & Deployment

Heimdall runs entirely for free using GitHub Actions and requires zero maintenance. To deploy your own instance:

1. Fork or clone this repository.
2. Go to your repository **Settings** -> **Secrets and variables** -> **Actions**.
3. Add the following Repository Secrets:
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: The entire raw JSON string of your Google Service Account.
   - `PAT_TOKEN`: Your GitHub Personal Access Token (must have `repo` and `workflow` scopes).
   - `GOOGLE_SHEET_ID`: The ID of your Google Sheet.
   - `GEMINI_API_KEY`: Your Gemini AI API Key.
   - `DISCORD_WEBHOOK_URL`: Your primary Discord webhook URL.
   - `DISCORD_WEBHOOK_URL_HIGH_PRIORITY`: Your secondary Discord webhook URL for priority alerts.
   - `DISCORD_WEBHOOK_URL_ISSUEHUNT`: Your third Discord webhook URL for IssueHunt bounties.
   - `ISSUEHUNT_SESSION_TOKEN`: (Optional) Your exported browser cookies in JSON format to log into IssueHunt.
4. The Heimdall cron jobs will automatically begin running every hour!
