# scripts/release_notes_generator.py
import os
import requests
import json
from datetime import datetime


# Environment Variables

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")  # e.g., "owner/repo"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BRANCH = os.getenv("GITHUB_REF", "refs/heads/main").split("/")[-1]

if not GITHUB_REPO or not GITHUB_TOKEN or not OPENROUTER_API_KEY:
    raise SystemExit("GITHUB_REPOSITORY, GITHUB_TOKEN, and OPENROUTER_API_KEY are required")

OWNER, REPO = GITHUB_REPO.split("/")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "release-notes-generator"
}


# Fetch commits & PRs

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


# Build prompt for AI

def build_prompt(messages):
    intro = (
        "You are an assistant that writes release notes. "
        "Format output as Markdown under headings: Features, Bug Fixes, Refactors/Improvements. "
        "Turn each change into a concise one-line bullet.\n\n"
    )
    payload = intro + "Messages:\n" + "\n".join(messages)
    return payload


# Call OpenRouter API

def call_openrouter(prompt):
    data = {
        "model": "gpt-4o-mini",  # change if needed
        "messages": [
            {"role": "system", "content": "You are a release-notes generator."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 800
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(data), timeout=60)
    r.raise_for_status()
    resp = r.json()
    return resp["choices"][0]["message"]["content"]


# Write release notes
def write_release_notes(text):
    header = f"# Release Notes\n\n_Generated: {datetime.utcnow().isoformat()}Z_\n\n"
    with open("RELEASE_NOTES.md", "w", encoding="utf-8") as f:
        f.write(header)
        f.write(text)
    print("✅ RELEASE_NOTES.md generated successfully!")


def main():
    print("Fetching commits and merged PRs...")
    commits = fetch_commits()
    prs = fetch_merged_prs()
    all_messages = commits + prs
    if not all_messages:
        print("No commits or PRs found for this branch.")
        return

    print("Building AI prompt...")
    prompt = build_prompt(all_messages)
    
    print("Calling OpenRouter to generate release notes...")
    notes = call_openrouter(prompt)

    write_release_notes(notes)

if __name__ == "__main__":
    main()
