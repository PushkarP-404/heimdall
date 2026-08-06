from google import genai
from src.config import GEMINI_API_KEY
import requests
import base64

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

class LLMAnalyzer:
    def __init__(self, github_headers):
        self.github_headers = github_headers
        self.repo_cache = {}

    def _fetch_file_content(self, repo_url, file_path):
        url = f"{repo_url}/contents/{file_path}"
        response = requests.get(url, headers=self.github_headers)
        if response.status_code == 200:
            content = response.json().get('content', '')
            if content:
                return base64.b64decode(content).decode('utf-8', errors='ignore')
        return ""

    def analyze_repo(self, repo_api_url):
        if repo_api_url in self.repo_cache:
            return self.repo_cache[repo_api_url]

        default_result = {"is_welcoming": True}
        if not client:
            return default_result

        readme = self._fetch_file_content(repo_api_url, "README.md")
        contributing = self._fetch_file_content(repo_api_url, "CONTRIBUTING.md")

        prompt = f"""
        You are an AI agent helping a developer find open source repositories.
        Read the provided README and CONTRIBUTING files.
        Determine if this repository actively welcomes external contributors.
        If it's deprecated, archived, or internal-only, answer NO. Otherwise, YES.
        
        Format your response EXACTLY as a single line:
        YES or NO

        README excerpt:
        {readme[:3000]}

        CONTRIBUTING excerpt:
        {contributing[:3000]}
        """
        try:
            print(f"  [LLM] Analyzing repository: {repo_api_url.split('repos/')[-1]}...")
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt
            )
            lines = [line.strip().upper() for line in response.text.strip().split('\n') if line.strip()]
            
            is_welcoming = "YES" in lines[0] if len(lines) > 0 else True
            
            result = {"is_welcoming": is_welcoming}
        except Exception as e:
            print(f"  [LLM] Repo Error: {e}")
            result = default_result
        
        self.repo_cache[repo_api_url] = result
        return result

    def analyze_issue(self, issue_title, issue_body):
        default_result = {"is_actionable": True, "effort": "LOW"}
        if not client:
            return default_result

        prompt = f"""
        You are an AI assisting a developer in finding actionable open source issues.
        Task 1: Determine if an external contributor can realistically work on it. (Vague questions or core-team-only tasks = NO, bugs/features = YES).
        Task 2: Determine the effort/attention required. Is this a very complex issue requiring deep architectural changes or significant effort? Answer HIGH if yes, LOW if it's relatively contained or standard.
        
        Format your response EXACTLY like this (2 lines):
        Line 1: YES or NO
        Line 2: HIGH or LOW

        Title: {issue_title}
        Body: {str(issue_body)[:2000]}
        """
        try:
            print(f"  [LLM] Analyzing issue viability: '{issue_title[:30]}...'")
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt
            )
            lines = [line.strip().upper() for line in response.text.strip().split('\n') if line.strip()]
            
            is_actionable = "YES" in lines[0] if len(lines) > 0 else True
            effort = "HIGH" if len(lines) > 1 and "HIGH" in lines[1] else "LOW"
            
            return {"is_actionable": is_actionable, "effort": effort}
        except Exception as e:
            print(f"  [LLM] Issue Error: {e}")
            return default_result
