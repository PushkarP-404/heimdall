import base64
import json
import re
import requests
from google import genai
from src.config import GEMINI_API_KEY, GEMINI_MODEL

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


def _clean_json_response(raw_text: str) -> str:
    """Clean markdown fences from LLM response text to parse pure JSON."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


class LLMAnalyzer:
    def __init__(self, github_headers):
        self.github_headers = github_headers
        self.repo_cache = {}

    def _fetch_file_content(self, repo_url, file_path):
        url = f"{repo_url}/contents/{file_path}"
        try:
            response = requests.get(url, headers=self.github_headers, timeout=10)
            if response.status_code == 200:
                content = response.json().get("content", "")
                if content:
                    return base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception:
            pass
        return ""

    def analyze_repo(self, repo_api_url):
        """Analyze README and CONTRIBUTING to ensure external contributors are welcomed."""
        if repo_api_url in self.repo_cache:
            return self.repo_cache[repo_api_url]

        default_result = {"is_welcoming": True, "notes": "Default accepted"}
        if not client:
            return default_result

        readme = self._fetch_file_content(repo_api_url, "README.md")
        contributing = self._fetch_file_content(repo_api_url, "CONTRIBUTING.md")

        # If neither file exists or both are empty, assume standard open source project
        if not readme and not contributing:
            result = {"is_welcoming": True, "notes": "No explicit guide"}
            self.repo_cache[repo_api_url] = result
            return result

        prompt = f"""
        You are an AI software engineering advisor.
        Examine the repository's documentation below.
        Determine if this repository welcomes external open source contributors.
        If it explicitly states it is private, read-only, archived, internal-only, or strictly rejects pull requests, answer NO.
        Otherwise, answer YES.

        Format your response as a single word: YES or NO

        README excerpt:
        {readme[:2500]}

        CONTRIBUTING excerpt:
        {contributing[:2500]}
        """

        try:
            repo_short = repo_api_url.split("repos/")[-1]
            print(f"  [LLM] Analyzing repo community friendliness: {repo_short}...")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            text = (response.text or "").strip().upper()
            is_welcoming = "NO" not in text

            result = {"is_welcoming": is_welcoming}
        except Exception as e:
            print(f"  [LLM] Repo Error: {e}")
            result = default_result

        self.repo_cache[repo_api_url] = result
        return result

    def analyze_issue(self, issue_title, issue_body, repo_name="", language=""):
        """
        Deep evaluation of issue quality and viability for open source contributors.
        Returns rich structured metadata including actionability, difficulty, effort,
        1-sentence summary, recommended skills, and a 1-10 quality score.
        """
        default_result = {
            "is_actionable": True,
            "difficulty": "Good First Issue",
            "category": "Bug",
            "estimated_effort": "Quick Fix (<2h)",
            "summary": issue_title,
            "recommended_skills": [language] if language else [],
            "quality_score": 7,
            "verdict_reason": "Standard issue",
        }

        if not client:
            return default_result

        prompt = f"""
        You are an elite open source developer evaluating GitHub issues for incoming contributors.
        Analyze this issue and produce an accurate, structured JSON evaluation.

        Repository: {repo_name}
        Primary Language: {language}
        Title: {issue_title}
        Body:
        {str(issue_body)[:3000]}

        Rules for evaluation:
        1. "is_actionable": false if the issue is a vague 1-line question, duplicates, or lacks clear context. true if there is a concrete bug to fix, feature to implement, test to add, or docs to improve.
        2. "difficulty": Choose exactly one of: "Good First Issue", "Intermediate", "Advanced".
        3. "category": Choose exactly one of: "Bug", "Feature", "Documentation", "Refactor", "Testing".
        4. "estimated_effort": Choose exactly one of: "Quick Fix (<2h)", "Moderate (1-2 days)", "Major (>3 days)".
        5. "summary": A crisp, 1-2 sentence TL;DR explaining exactly what the task requires.
        6. "recommended_skills": List 1 to 4 relevant languages, tools, or frameworks (e.g. ["Python", "FastAPI"]).
        7. "quality_score": Integer 1 to 10 (1 = junk/vague, 10 = immaculate description with reproduction/pointers).
        8. "verdict_reason": One concise sentence explaining why this issue is or isn't recommended.

        Respond with ONLY a raw JSON object matching this schema (no markdown, no extra text):
        {{
            "is_actionable": true,
            "difficulty": "Good First Issue",
            "category": "Bug",
            "estimated_effort": "Quick Fix (<2h)",
            "summary": "...",
            "recommended_skills": ["..."],
            "quality_score": 8,
            "verdict_reason": "..."
        }}
        """

        try:
            print(f"  [LLM] Evaluating issue quality: '{issue_title[:35]}...'")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )

            cleaned_text = _clean_json_response(response.text or "")
            parsed = json.loads(cleaned_text)

            # Ensure all required keys exist with reasonable defaults
            return {
                "is_actionable": bool(parsed.get("is_actionable", True)),
                "difficulty": str(parsed.get("difficulty", "Good First Issue")),
                "category": str(parsed.get("category", "Bug")),
                "estimated_effort": str(parsed.get("estimated_effort", "Quick Fix (<2h)")),
                "summary": str(parsed.get("summary", issue_title)),
                "recommended_skills": list(parsed.get("recommended_skills", [language] if language else [])),
                "quality_score": int(parsed.get("quality_score", 7)),
                "verdict_reason": str(parsed.get("verdict_reason", "Actionable open source issue")),
            }
        except Exception as e:
            print(f"  [LLM] Issue Analysis Exception: {e}")
            return default_result
