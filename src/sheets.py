import gspread
from src.config import GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_SHEET_ID

class GoogleSheetsManager:
    def __init__(self):
        try:
            self.gc = gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_FILE)
            self.sheet = self.gc.open_by_key(GOOGLE_SHEET_ID).sheet1
            self._ensure_headers()
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            self.sheet = None

    def _ensure_headers(self):
        # Check if the first row is empty, if so, add headers
        if not self.sheet.row_values(1):
            headers = ["Repository", "Issue URL", "Title", "Labels", "Date Found", "Status"]
            self.sheet.append_row(headers)

    def get_existing_issue_urls(self):
        if not self.sheet:
            return set()
        
        # Get all values from the 'Issue URL' column (which is the 2nd column)
        try:
            urls = self.sheet.col_values(2)
            # Skip the header row
            return set(urls[1:]) if len(urls) > 1 else set()
        except Exception as e:
            print(f"Error getting existing issues: {e}")
            return set()

    def append_issues(self, issues):
        if not self.sheet or not issues:
            return

        rows_to_append = []
        for issue in issues:
            labels = ", ".join([label['name'] for label in issue.get('labels', [])])
            repo_name = issue['repository_url'].split('repos/')[-1]
            rows_to_append.append([
                repo_name,
                issue['html_url'],
                issue['title'],
                labels,
                issue['created_at'],
                "New"
            ])

        try:
            self.sheet.append_rows(rows_to_append)
            print(f"Successfully appended {len(rows_to_append)} new issues to the sheet.")
        except Exception as e:
            print(f"Error appending issues to sheet: {e}")
