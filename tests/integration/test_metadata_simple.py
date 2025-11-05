#!/usr/bin/env python3
"""
Simple test to check if chat_interface can handle metadata properly.
"""

from agent_chat_cli.chat_interface import render_answer
import json

# Simulate what the agent would return for "create a github issue"
print("=" * 80)
print("SIMULATED AGENT RESPONSE TEST")
print("=" * 80)
print()
print("Testing scenario: User asks 'create a github issue'")
print("Agent should ask for clarification (GitHub vs Jira)")
print("Then after clarification, agent should return metadata for required fields")
print()
print("=" * 80)
print()

# Test 1: Clarification response (no metadata yet)
print("TEST 1: Clarification Response")
print("-" * 80)
clarification_response = """I can create an issue in either GitHub or Jira. Which would you prefer?

- **GitHub Issue** - For code repository issues, bug tracking, feature requests
- **Jira Ticket** - For project management, sprint planning, formal issue tracking

Please let me know which platform you'd like to use."""

print("Agent Response:")
render_answer(clarification_response, agent_name="AI Platform Engineer")

# Test 2: Metadata response after user chooses GitHub
print()
print("=" * 80)
print("TEST 2: Metadata Response (User chose GitHub)")
print("-" * 80)

metadata_response = json.dumps({
    "content": "To create a GitHub issue, I need the following information:",
    "is_task_complete": False,
    "require_user_input": True,
    "metadata": {
        "user_input": True,
        "input_fields": [
            {
                "field_name": "repository",
                "field_description": "GitHub repository (format: owner/repo)",
                "field_values": None
            },
            {
                "field_name": "title", 
                "field_description": "Brief summary of the issue",
                "field_values": None
            },
            {
                "field_name": "labels",
                "field_description": "Issue labels",
                "field_values": ["bug", "enhancement", "documentation", "question"]
            }
        ]
    }
})

print()
print("Agent Response (JSON with metadata):")
print()

# Parse and display
try:
    structured = json.loads(metadata_response)
    print("✅ Successfully parsed structured response")
    print(f"   - Content: {structured.get('content')}")
    print(f"   - Requires input: {structured.get('require_user_input')}")
    print(f"   - Fields: {len(structured.get('metadata', {}).get('input_fields', []))}")
    print()
except json.JSONDecodeError:
    structured = None
    print("❌ Failed to parse JSON response")

# Render it
print("Rendered output:")
print()
render_answer(metadata_response, agent_name="AI Platform Engineer")

print()
print("=" * 80)
print("✅ METADATA TEST COMPLETED")
print("=" * 80)
print()
print("Expected behavior:")
print("1. Content displayed in panel (NOT raw JSON)")
print("2. Each input field shown as styled question")
print("3. Fields with field_values shown as dropdown options")
print("4. Fields without field_values shown as text input prompts")
print()

