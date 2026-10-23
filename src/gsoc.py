import json
import re
import requests

GSOC_API_URL = "https://api.gsocorganizations.dev/organizations.json"

_gsoc_org_names: set[str] | None = None

# Curated list of well-known GSoC participating organizations and umbrella foundations
# that frequently use custom web domains rather than direct github.com in API fields
CURATED_GSOC_ORGS: set[str] = {
    "psf",
    "python",
    "apache",
    "mozilla",
    "wikimedia",
    "torproject",
    "sympy",
    "scikit-learn",
    "oppia",
    "zulip",
    "cern",
    "metabrainz",
    "jenkins-infra",
    "jenkinsci",
    "godotengine",
    "audacity",
    "videolan",
    "neovim",
    "coala",
    "freebsd",
    "inkscape",
    "blender",
    "kicad",
    "opensuse",
    "fedora-infra",
    "redhat",
    "kubernetes",
    "cncf",
    "llvm",
    "gcc-mirror",
    "qemu",
    "git",
    "curl",
    "wireshark",
    "libreoffice",
    "gnome",
    "kde",
    "open-telemetry",
    "prometheus",
    "grpc",
    "envoyproxy",
    "containrrr",
}


def _extract_github_org(url: str) -> str | None:
    """Extract the GitHub org/user name from a GitHub URL."""
    if not url:
        return None
    url = url.rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if url.startswith(prefix):
            remainder = url[len(prefix):]
            return remainder.split("/")[0].lower()
    return None


def get_gsoc_github_orgs() -> set[str]:
    """
    Fetch the list of all GSoC organizations from the public API combined
    with curated open-source umbrella foundations.
    Cached in-process.
    """
    global _gsoc_org_names
    if _gsoc_org_names is not None:
        return _gsoc_org_names

    names: set[str] = set(CURATED_GSOC_ORGS)

    print("Fetching GSoC organization list from api.gsocorganizations.dev ...")
    try:
        resp = requests.get(GSOC_API_URL, timeout=30)
        resp.raise_for_status()
        orgs = resp.json()

        # Extract GitHub URLs from the full JSON payload
        orgs_str = json.dumps(orgs)
        pattern = re.compile(r'github\.com/([a-zA-Z0-9-]+)')
        for match in pattern.finditer(orgs_str):
            names.add(match.group(1).lower())

    except Exception as e:
        print(f"  [GSoC] WARNING: Could not fetch GSoC org list: {e}. Using curated set ({len(names)} orgs).")

    _gsoc_org_names = names
    print(f"  [GSoC] Total {len(_gsoc_org_names)} GSoC GitHub orgs loaded and active.")
    return _gsoc_org_names


def is_gsoc_org(repo_api_url: str) -> bool:
    """
    Given a GitHub API repo URL like
    'https://api.github.com/repos/ORG/REPO', return True if
    ORG is a known GSoC participant.
    """
    try:
        parts = repo_api_url.rstrip("/").split("/")
        owner = parts[-2].lower()
    except (IndexError, AttributeError):
        return False
    return owner in get_gsoc_github_orgs()
