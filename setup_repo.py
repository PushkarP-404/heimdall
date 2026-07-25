import os
import requests
import subprocess
from dotenv import load_dotenv

def main():
    load_dotenv()
    TOKEN = os.getenv('GITHUB_TOKEN')
    
    if not TOKEN:
        print("GITHUB_TOKEN not found in .env")
        return

    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    print("Creating private repository 'heimdall-issue-finder' on GitHub...")
    repo_data = {
        "name": "heimdall-issue-finder",
        "description": "An autonomous AI agent that finds and filters GitHub issues.",
        "private": True
    }

    resp = requests.post("https://api.github.com/user/repos", headers=headers, json=repo_data)
    
    if resp.status_code == 201:
        repo_info = resp.json()
        print(f"Created repository: {repo_info['html_url']}")
        clone_url = repo_info['clone_url']
        html_url = repo_info['html_url']
    elif resp.status_code == 422:
        user_resp = requests.get("https://api.github.com/user", headers=headers)
        username = user_resp.json()['login']
        clone_url = f"https://github.com/{username}/heimdall-issue-finder.git"
        html_url = f"https://github.com/{username}/heimdall-issue-finder"
        print(f"Repository already exists. Using {clone_url}")
    else:
        print(f"Failed to create repo: {resp.text}")
        return

    # Inject token into clone URL for push auth
    auth_url = clone_url.replace("https://", f"https://{TOKEN}@")

    print("Initializing Git...")
    subprocess.run(["git", "init"])
    subprocess.run(["git", "branch", "-M", "main"])
    
    # Check if anything to commit
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if status.stdout.strip():
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Initial commit of Heimdall Agent"])
    
    subprocess.run(["git", "remote", "remove", "origin"], stderr=subprocess.DEVNULL)
    subprocess.run(["git", "remote", "add", "origin", auth_url])
    
    print("Pushing to GitHub...")
    res = subprocess.run(["git", "push", "-u", "origin", "main"])
    if res.returncode == 0:
        print(f"\nSUCCESS! Your code is now hosted at: {html_url}")
        print("Please remember to go to Settings -> Secrets and variables -> Actions to add your Secrets!")
    else:
        print("\nFailed to push code.")

if __name__ == "__main__":
    main()
