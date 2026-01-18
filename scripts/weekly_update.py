#!/usr/bin/env python3
"""
Weekly ROI Calculator Update Script
Uses Claude API to research and update GPU pricing and model information.
"""

import os
import json
import anthropic
from datetime import datetime

CONFIG_FILE = 'roi-config Rev 08.json'
HTML_FILE = 'F5_DPU_ROI_Calculator_F5Branded_v2.8_optimized.html'

UPDATE_PROMPT = """You are updating an F5 DPU ROI Calculator configuration file.

Current date: {date}
Current config version: {version}

TASK: Research and provide updated values for GPU pricing and new models in JSON format.

Return ONLY a JSON object with:
{
  "version_increment": "patch|minor",
  "gpu_updates": {},
  "new_gpus": {},
  "new_models": {},
  "notes": "Summary of changes"
}
"""

def get_claude_updates(current_config):
    """Call Claude API to get update recommendations."""
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": UPDATE_PROMPT.format(
                date=datetime.now().strftime("%Y-%m-%d"),
                version=current_config.get("version", "unknown")
            )
        }]
    )

    response_text = message.content[0].text
    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        else:
            json_str = response_text
        return json.loads(json_str.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {e}")
        return None

def increment_version(version, increment_type="patch"):
    """Increment semantic version."""
    parts = version.split(".")
    if len(parts) == 3:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        if increment_type == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1
        return f"{major}.{minor}.{patch}"
    return version

def apply_updates(config, updates):
    """Apply updates to the configuration."""
    if not updates:
        print("No updates to apply")
        return config, False

    changes_made = False
    if updates.get("version_increment"):
        old_version = config.get("version", "1.0.0")
        config["version"] = increment_version(old_version, updates["version_increment"])
        changes_made = True
        print(f"Version: {old_version} -> {config['version']}")

    config["lastUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    return config, changes_made

def main():
    print(f"=== Weekly ROI Calculator Update ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Config file not found: {CONFIG_FILE}")
        return 1

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    print(f"Current version: {config.get('version', 'unknown')}")

    print("Fetching updates from Claude API...")
    updates = get_claude_updates(config)

    if updates:
        print(f"Update notes: {updates.get('notes', 'No notes')}")
        config, changes_made = apply_updates(config, updates)

        if changes_made:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            print(f"Saved updates to {CONFIG_FILE}")
        else:
            print("No changes were needed")
    else:
        print("Failed to get updates from Claude API")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
