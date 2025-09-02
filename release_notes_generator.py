# Save this file as release_notes_generator.py

import argparse
import os
import re
import requests
from github import Github, GithubException

class ServiceNowClient:
    # ... (ServiceNowClient class remains unchanged) ...
    """A client to interact with the ServiceNow API."""
    def __init__(self, instance, user, password):
        if not instance or not user or not password:
            raise ValueError("ServiceNow instance, user, and password are required.")
        self.base_url = f"https://{instance}.service-now.com/api/now/table"
        self.auth = (user, password)

    def get_story_details(self, story_number):
        """Fetches a story using its public number."""
        print(f"Fetching details for story: {story_number} from ServiceNow...")
        url = f"{self.base_url}/sn_safe_story"
        params = {"sysparm_query": f"number={story_number}", "sysparm_fields": "number,short_description"}
        try:
            response = requests.get(url, auth=self.auth, params=params, timeout=15)
            response.raise_for_status()
            data = response.json().get('result')
            return data[0] if data else None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching story {story_number}: {e}")
            return None

def parse_args():
    # ... (parse_args function remains unchanged) ...
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate categorized release notes from ServiceNow and GitHub.")
    parser.add_argument("--repo", required=True, help="GitHub repo in format org/repo.")
    parser.add_argument("--from-tag", required=True, help="The starting git tag (older version).")
    parser.add_argument("--to-tag", required=True, help="The ending git tag (newer version).")
    parser.add_argument("--servicenow-instance", required=True, help="Your ServiceNow instance name.")
    parser.add_argument("--story-id", required=True, help="The ServiceNow Story ID for this release.")
    return parser.parse_args()

def generate_release_note_from_ai(story, categories, gemini_key, to_tag):
    """Builds a rich prompt and calls the Gemini API."""
    context = ""
    if story:
        context += f"## Business Context (from ServiceNow)\n- **User Story:** {story.get('number', 'N/A')} - {story.get('short_description', 'N/A')}\n\n"
    context += "## Technical Implementation (from Git Commits)\n"
    has_changes = False
    if categories["features"]:
        context += "### ✨ New Features\n" + "\n".join(categories["features"]) + "\n\n"; has_changes = True
    if categories["fixes"]:
        context += "### 🐛 Bug Fixes\n" + "\n".join(categories["fixes"]) + "\n\n"; has_changes = True
    if categories["performance"]:
        context += "### ⚡️ Performance Improvements\n" + "\n".join(categories["performance"]) + "\n\n"; has_changes = True
    if not has_changes:
        context += "No specific user-facing code changes were categorized.\n"

    # --- NEW PROMPT EMBEDDED AS REQUESTED ---
    prompt = f"""
You are an expert technical writer tasked with creating a professional release note for version '{to_tag}'.

You are provided with two sources of input:
1. **Business Context** – from ServiceNow (stories, tasks, PIs). This explains the purpose and value from the user's perspective.
2. **Technical Implementation** – from GitHub commit history. This provides the exact technical changes made.

### Instructions:
1. **Executive Summary**
   - Begin with a user-friendly summary of the release, explaining the new capabilities or fixes from the ServiceNow stories.
   - Clearly connect these stories to their business value.

2. **Detailed Release Notes**
   - Create structured sections such as **New Features**, **Improvements**, and **Bug Fixes**.
   - For each item, combine **ServiceNow data** (story/task title, description, business purpose) with **GitHub commit details** (actual code or config changes).
   - Ensure both perspectives are visible — e.g., start with the business need (story), then show the supporting technical work (commits).

3. **Formatting**
   - Use Markdown with headings, bullet points, and sub-sections.
   - Be concise and professional.
   - Do not simply list commits or stories separately — weave them into a single narrative.

### Input Data
{context.strip()}
"""

    print("Sending your detailed prompt to Gemini AI...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60) # Increased timeout for complex prompt
        response.raise_for_status()
        result = response.json()
        release_note = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", None)
        return release_note.strip() if release_note else f"# Release Notes for {to_tag}\n\nCould not generate AI summary."
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return f"# Release Notes for {to_tag}\n\nAI summary generation failed."

def main():
    # ... (main function remains unchanged) ...
    args = parse_args()
    sn_user = os.environ.get("SN_USER")
    sn_pass = os.environ.get("SN_PASSWORD")
    gh_token = os.environ.get("GITHUB_TOKEN")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([sn_user, sn_pass, gh_token, gemini_key]):
        print("Error: Ensure all required environment variables are set.")
        return

    sn_client = ServiceNowClient(args.servicenow_instance, sn_user, sn_pass)
    story_data = sn_client.get_story_details(args.story_id) if args.story_id else None

    commits = []
    try:
        g = Github(gh_token)
        repo = g.get_repo(args.repo)
        comparison = repo.compare(base=args.from_tag, head=args.to_tag)
        commits = list(comparison.commits)
    except GithubException as e:
        print(f"Error fetching commits from GitHub: {e}")

    print(f"Found {len(commits)} commits. Categorizing now...")
    categories = {"features": [], "fixes": [], "performance": [], "internal": []}
    commit_pattern = re.compile(r"^(feat|fix|perf|refactor|chore|ci|docs|style|test)(?:\(([\w\s-]+)\))?:\s(.+)")

    for commit in commits:
        message = commit.commit.message.split('\n')[0]
        match = commit_pattern.match(message)
        if match:
            commit_type, scope, description = match.groups()
            formatted_message = f"- **{scope.capitalize() if scope else 'General'}:** {description}"
            if commit_type == "feat": categories["features"].append(formatted_message)
            elif commit_type == "fix": categories["fixes"].append(formatted_message)
            elif commit_type == "perf": categories["performance"].append(formatted_message)
            elif commit_type in ["refactor", "chore", "ci", "style"]: categories["internal"].append(formatted_message)
    
    release_note_content = generate_release_note_from_ai(story_data, categories, gemini_key, args.to_tag)

    filename = f"release_notes_{args.to_tag}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(release_note_content)
    
    print(f"\n✅ Successfully generated final release notes: {filename}")
    print("\n--- Generated Content ---\n")
    print(release_note_content)

if __name__ == "__main__":
    main()