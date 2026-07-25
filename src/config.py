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
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_WEBHOOK_URL_HIGH_PRIORITY = os.getenv("DISCORD_WEBHOOK_URL_HIGH_PRIORITY")

# Search Parameters
SEARCH_TAGS = ["good first issue", "help wanted", "bug", "enhancement", "improvement"]
