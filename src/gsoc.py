import json
import re
import requests

GSOC_API_URL = "https://api.gsocorganizations.dev/organizations.json"

_gsoc_org_names: set[str] | None = None


def _extract_github_org(url: str) -> str | None:
    """Extract the GitHub org/user name from a GitHub URL."""
    if not url:
        return None
    url = url.rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if url.startswith(prefix):
            remainder = url[len(prefix):]
            # Take only the first path segment (the org/user name)
            return remainder.split("/")[0].lower()
    return None


def get_gsoc_github_orgs() -> set[str]:
    """
    Fetch the list of all GSoC organizations from the public API and return
    a set of lowercase GitHub org names for fast membership testing.

    Results are cached in-process so the API is only hit once per run.
    """
    global _gsoc_org_names
    if _gsoc_org_names is not None:
        return _gsoc_org_names

    print("Fetching GSoC organization list from api.gsocorganizations.dev ...")
    try:
        resp = requests.get(GSOC_API_URL, timeout=30)
        resp.raise_for_status()
        orgs = resp.json()
    except Exception as e:
        print(f"  [GSoC] WARNING: Could not fetch GSoC org list: {e}. Falling back to empty set.")
        _gsoc_org_names = set()
        return _gsoc_org_names

    names: set[str] = set()
    
    # Dump the entire response to a string to easily find all github.com URLs
    # This catches orgs that put their GitHub URL in ideas_url, guide_url, or student project code_urls
    orgs_str = json.dumps(orgs)
    pattern = re.compile(r'github\.com/([a-zA-Z0-9-]+)')
    for match in pattern.finditer(orgs_str):
        names.add(match.group(1).lower())

    _gsoc_org_names = names
    print(f"  [GSoC] Loaded {len(names)} GSoC GitHub orgs.")
    return _gsoc_org_names


def is_gsoc_org(repo_api_url: str) -> bool:
    """
    Given a GitHub API repo URL like
    'https://api.github.com/repos/ORG/REPO', return True if
    ORG is a known GSoC participant.
    """
    # repo_api_url looks like https://api.github.com/repos/{owner}/{repo}
    try:
        parts = repo_api_url.rstrip("/").split("/")
        # parts[-2] is the owner, parts[-1] is the repo name
        owner = parts[-2].lower()
    except (IndexError, AttributeError):
        return False
    return owner in get_gsoc_github_orgs()
