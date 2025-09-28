# scripts/generate_release_notes.py
import os
import requests
import json
from datetime import datetime

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise SystemExit("OPENROUTER_API_KEY environment variable is required")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def load_messages():
    if not os.path.exists("messages.txt"):
        raise SystemExit("messages.txt not found. Run fetch_commits_prs.py first.")
    with open("messages.txt", "r", encoding="utf-8") as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def build_prompt(messages):
    intro = (
        "You are an assistant that writes release notes. "
        "Format output as Markdown under headings: Features, Bug Fixes, Refactors/Improvements. "
        "Turn each change into a concise one-line bullet.\n\n"
    )
    payload = intro + "Messages:\n" + "\n".join(messages)
    return payload

def call_openrouter(prompt):
    data = {
        "model": "gpt-4o-mini",   # change this to a model available to your OpenRouter account if needed
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

def write_release_notes(text):
    header = f"# Release Notes\n\n_Generated: {datetime.utcnow().isoformat()}Z_\n\n"
    with open("RELEASE_NOTES.md", "w", encoding="utf-8") as f:
        f.write(header)
        f.write(text)
    print("Wrote RELEASE_NOTES.md")

def main():
    messages = load_messages()
    prompt = build_prompt(messages)
    print("Calling OpenRouter to generate release notes...")
    notes = call_openrouter(prompt)
    write_release_notes(notes)

if __name__ == "__main__":
    main()
