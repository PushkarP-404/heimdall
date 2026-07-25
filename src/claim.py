import os
import requests
import google.generativeai as genai
from src.config import PAT_TOKEN, GEMINI_API_KEY
from src.sheets import GoogleSheetsManager

ISSUE_URL = os.getenv("ISSUE_URL")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

def main():
    if not ISSUE_URL:
        print("No ISSUE_URL provided.")
        return

    print(f"Attempting to claim issue: {ISSUE_URL}")
    
    parts = ISSUE_URL.split('/')
    owner, repo, issue_number = parts[-4], parts[-3], parts[-1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {PAT_TOKEN}"
    }

    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch issue details.")
        return
        
    issue_data = response.json()
    
    if model:
        prompt = f"""
        You are an experienced, polite software engineer attempting to claim an open source issue on GitHub.
        Write a concise, professional comment asking to be assigned to this issue.
        Do NOT write a generic bot-like response. Keep it strictly to 1-2 sentences. 
        Example: "Hi, I'd love to take a look at this if no one else is working on it!"
        
        Issue Title: {issue_data['title']}
        Issue Body: {str(issue_data.get('body'))[:1000]}
        """
        try:
            comment_body = model.generate_content(prompt).text.strip()
        except Exception:
            comment_body = "Hi, I'd like to take this on! Please let me know if there's any specific context I should be aware of."
    else:
        comment_body = "Hi, I'd like to take this on! Please let me know if there's any specific context I should be aware of."

    print(f"Drafted Comment: {comment_body}")
    
    # Post the comment
    comment_url = f"{api_url}/comments"
    post_resp = requests.post(comment_url, headers=headers, json={"body": comment_body})
    
    if post_resp.status_code == 201:
        print("Successfully posted claim comment!")
        
        # Update Google Sheets status
        try:
            sheets_manager = GoogleSheetsManager()
            if sheets_manager.sheet:
                cell = sheets_manager.sheet.find(ISSUE_URL)
                if cell:
                    sheets_manager.sheet.update_cell(cell.row, 6, "Claimed")
                    print("Updated Google Sheet status to 'Claimed'.")
        except Exception as e:
            print(f"Failed to update Google Sheet: {e}")
            
    else:
        print(f"Failed to post comment: {post_resp.status_code} - {post_resp.text}")

if __name__ == "__main__":
    main()
