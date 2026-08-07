import gspread
from datetime import datetime, timezone
from src.config import GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_SHEET_ID


class GoogleSheetsManager:
    def __init__(self):
        self.gc = None
        self.sheet = None
        self.issuehunt_sheet = None
        try:
            self.gc = gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_FILE)
            spreadsheet = self.gc.open_by_key(GOOGLE_SHEET_ID)
            self.sheet = spreadsheet.sheet1
            self._ensure_headers(
                self.sheet,
                ["Repository", "Issue URL", "Title", "Labels", "Date Found", "Status"],
            )
            self.issuehunt_sheet = self._get_or_create_worksheet(
                spreadsheet,
                "IssueHunt",
                ["URL", "Title", "Amount", "Date Found"],
            )
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _ensure_headers(self, sheet, headers):
        """Add a header row to *sheet* if it is completely empty."""
        if not sheet.row_values(1):
            sheet.append_row(headers)

    def _get_or_create_worksheet(self, spreadsheet, name, headers):
        """Return an existing worksheet or create it with header row."""
        try:
            ws = spreadsheet.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(headers))
            ws.append_row(headers)
        return ws

    # -------------------------------------------------------------------------
    # Main-agent issue tracking
    # -------------------------------------------------------------------------

    def get_existing_issue_urls(self):
        """Return a set of all Issue URLs already in the main sheet (col 2)."""
        if not self.sheet:
            return set()
        try:
            urls = self.sheet.col_values(2)
            # Skip the header row
            return set(urls[1:]) if len(urls) > 1 else set()
        except Exception as e:
            print(f"Error getting existing issues: {e}")
            return set()

    def append_issues(self, issues):
        """Batch-append new issues to the main sheet."""
        if not self.sheet or not issues:
            return

        rows_to_append = []
        for issue in issues:
            labels = ", ".join([label["name"] for label in issue.get("labels", [])])
            repo_name = issue["repository_url"].split("repos/")[-1]
            rows_to_append.append(
                [
                    repo_name,
                    issue["html_url"],
                    issue["title"],
                    labels,
                    issue["created_at"],
                    "New",
                ]
            )

        try:
            self.sheet.append_rows(rows_to_append)
            print(f"Successfully appended {len(rows_to_append)} new issues to the sheet.")
        except Exception as e:
            print(f"Error appending issues to sheet: {e}")

    def update_issue_status(self, issue_url, status):
        """Find a row by Issue URL (col 2) and update its Status (col 6)."""
        if not self.sheet:
            print("Sheet not connected, skipping status update.")
            return
        try:
            cell = self.sheet.find(issue_url, in_column=2)
            if cell:
                self.sheet.update_cell(cell.row, 6, status)
                print(f"Updated status for {issue_url} to '{status}'.")
            else:
                print(f"Could not find issue URL in sheet to update: {issue_url}")
        except Exception as e:
            print(f"Error updating issue status: {e}")

    # -------------------------------------------------------------------------
    # IssueHunt bounty deduplication
    # -------------------------------------------------------------------------

    def get_existing_bounty_urls(self):
        """Return a set of already-seen IssueHunt bounty URLs (col 1)."""
        if not self.issuehunt_sheet:
            return set()
        try:
            urls = self.issuehunt_sheet.col_values(1)
            # Skip the header row
            return set(urls[1:]) if len(urls) > 1 else set()
        except Exception as e:
            print(f"Error getting existing bounty URLs: {e}")
            return set()

    def append_bounties(self, bounties):
        """Log new bounties to the IssueHunt sheet tab for future deduplication."""
        if not self.issuehunt_sheet or not bounties:
            return
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = [
            [b.get("url", ""), b.get("title", ""), b.get("amount", ""), now]
            for b in bounties
        ]
        try:
            self.issuehunt_sheet.append_rows(rows)
            print(f"Logged {len(rows)} new bounties to the IssueHunt sheet tab.")
        except Exception as e:
            print(f"Error appending bounties to sheet: {e}")
