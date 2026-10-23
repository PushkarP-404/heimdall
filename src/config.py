import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# GitHub Configuration
PAT_TOKEN = os.getenv("PAT_TOKEN")

# Google Sheets Configuration
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Agent Brain & Notifications
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_WEBHOOK_URL_HIGH_PRIORITY = os.getenv("DISCORD_WEBHOOK_URL_HIGH_PRIORITY")
DISCORD_WEBHOOK_URL_ISSUEHUNT = os.getenv("DISCORD_WEBHOOK_URL_ISSUEHUNT")

# IssueHunt Web Scraping
ISSUEHUNT_SESSION_TOKEN = os.getenv("ISSUEHUNT_SESSION_TOKEN")

# Discovery & Quality Thresholds
MIN_STARS = int(os.getenv("MIN_STARS", "30"))  # Baseline stars for curated beginner issues
MIN_STARS_BROAD = int(os.getenv("MIN_STARS_BROAD", "300"))  # Minimum stars for broad labels (bug/enhancement)
HIGH_PRIORITY_STARS = int(os.getenv("HIGH_PRIORITY_STARS", "1000"))
MAX_COMMENTS = int(os.getenv("MAX_COMMENTS", "5"))  # Skip crowded/claimed issues
MIN_BODY_LENGTH = int(os.getenv("MIN_BODY_LENGTH", "30"))  # Skip empty or 1-line vague issues
MIN_QUALITY_SCORE = int(os.getenv("MIN_QUALITY_SCORE", "6"))  # LLM quality score (1-10)

# Optional Target Languages (e.g. "python,typescript,javascript,go")
TARGET_LANGUAGES = [
    lang.strip().lower()
    for lang in os.getenv("TARGET_LANGUAGES", "").split(",")
    if lang.strip()
]

# Curated tags and broad tags
CURATED_BEGINNER_TAGS = ["good first issue", "help wanted", "first-timers-only", "up-for-grabs"]
BROAD_TAGS = ["bug", "enhancement"]
SEARCH_TAGS = CURATED_BEGINNER_TAGS + BROAD_TAGS

# Labels to exclude (meta, invalid, blocked, questions)
EXCLUDE_LABELS = {
    "wontfix", "invalid", "duplicate", "question", "blocked",
    "stale", "needs reproduction", "discussion", "waiting for response"
}
