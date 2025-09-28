# scripts/fetch_commits_prs.py
import os
import requests

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")  # owner/repo (set by Actions)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")      # set by Actions
BRANCH = os.getenv("GITHUB_REF", "refs/heads/main").split("/")[-1]

if not GITHUB_REPO or not GITHUB_TOKEN:
    raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN must be set as env vars")

OWNER, REPO = GITHUB_REPO.split("/")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "release-notes-generator"
}

def fetch_commits():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits"
    params = {"sha": BRANCH, "per_page": 50}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    commits = r.json()
    messages = []
    for c in commits:
        sha = c.get("sha", "")[:7]
        msg = c.get("commit", {}).get("message", "").splitlines()[0]
        messages.append(f"{sha}: {msg}")
    return messages

def fetch_merged_prs():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
    params = {"state": "closed", "per_page": 50, "sort": "updated", "direction": "desc"}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    prs = r.json()
    merged = []
    for pr in prs:
        if pr.get("merged_at"):
            merged.append(f"PR #{pr['number']}: {pr['title']}")
    return merged

def main():
    commits = fetch_commits()
    prs = fetch_merged_prs()
    all_msgs = commits + prs
    with open("messages.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_msgs))
    print(f"Wrote {len(all_msgs)} messages to messages.txt")

if __name__ == "__main__":
    main()
