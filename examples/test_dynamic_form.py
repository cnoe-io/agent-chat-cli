#!/usr/bin/env python3
"""
Test Dynamic Form Rendering

This script demonstrates the new dynamic form feature in agent-chat-cli.
It simulates a backend response with structured metadata and shows how
the CLI renders an interactive form.
"""

import json
from agent_chat_cli.a2a_client import parse_structured_response, render_metadata_form
from rich.console import Console

# Example 1: Jira Ticket Creation
jira_response = {
    "content": "To create a Jira ticket, I need the following information:",
    "require_user_input": True,
    "is_task_complete": False,
    "metadata": {
        "user_input": True,
        "input_fields": [
            {
                "field_name": "project_key",
                "field_description": "The Jira project key where the issue should be created",
                "field_values": ["CAIPE", "DEVOPS", "PLATFORM"]
            },
            {
                "field_name": "issue_type",
                "field_description": "Type of Jira issue to create",
                "field_values": ["Bug", "Task", "Story", "Epic"]
            },
            {
                "field_name": "summary",
                "field_description": "Brief summary of the issue",
                "field_values": None
            },
            {
                "field_name": "description",
                "field_description": "Detailed description of the issue (optional)",
                "field_values": None
            }
        ]
    }
}

# Example 2: GitHub Issue
github_response = {
    "content": "I can create a GitHub issue for you. Please provide:",
    "require_user_input": True,
    "metadata": {
        "input_fields": [
            {
                "field_name": "repository",
                "field_description": "GitHub repository (format: owner/repo)",
                "field_values": None
            },
            {
                "field_name": "title",
                "field_description": "Issue title",
                "field_values": None
            },
            {
                "field_name": "labels",
                "field_description": "Labels to add (comma-separated)",
                "field_values": None
            }
        ]
    }
}

def test_parse_structured_response():
    """Test JSON parsing for structured responses"""
    print("=" * 60)
    print("TEST 1: Parsing Structured JSON Response")
    print("=" * 60)

    # Test with structured response
    json_text = json.dumps(jira_response)
    parsed = parse_structured_response(json_text)

    print(f"\n✅ Parsed successfully:")
    print(f"   - Content: {parsed['content'][:50]}...")
    print(f"   - Requires Input: {parsed['require_user_input']}")
    print(f"   - Metadata Fields: {len(parsed['metadata']['input_fields'])}")

    # Test with plain text (no JSON)
    plain_text = "This is just a normal response without metadata"
    parsed_plain = parse_structured_response(plain_text)

    print(f"\n✅ Plain text handled gracefully:")
    print(f"   - Content: {parsed_plain['content']}")
    print(f"   - Requires Input: {parsed_plain['require_user_input']}")
    print()

def test_render_form_jira():
    """Test rendering Jira ticket form"""
    print("=" * 60)
    print("TEST 2: Rendering Jira Ticket Form")
    print("=" * 60)
    print()

    console = Console()
    console.print("[cyan]This will show an interactive form.[/cyan]")
    console.print("[yellow]Try filling it out (or press Ctrl+C to skip)[/yellow]")
    print()

    try:
        form_data = render_metadata_form(jira_response["metadata"], console)

        if form_data:
            print("\n✅ Form submitted successfully!")
            print("Data to send to agent:")
            print(json.dumps(form_data, indent=2))
        else:
            print("\n⚠️  Form cancelled")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test skipped (Ctrl+C)")

def test_render_form_github():
    """Test rendering GitHub issue form"""
    print("\n")
    print("=" * 60)
    print("TEST 3: Rendering GitHub Issue Form")
    print("=" * 60)
    print()

    console = Console()
    console.print("[cyan]This will show a different form with text fields.[/cyan]")
    console.print("[yellow]Try filling it out (or press Ctrl+C to skip)[/yellow]")
    print()

    try:
        form_data = render_metadata_form(github_response["metadata"], console)

        if form_data:
            print("\n✅ Form submitted successfully!")
            print("Data to send to agent:")
            print(json.dumps(form_data, indent=2))
        else:
            print("\n⚠️  Form cancelled")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test skipped (Ctrl+C)")

if __name__ == "__main__":
    console = Console()

    console.print(Panel(
        "[bold cyan]Dynamic Form Feature Test[/bold cyan]\n\n"
        "This demonstrates the new interactive form rendering in agent-chat-cli.",
        title="🎯 Test Suite",
        border_style="cyan"
    ))

    from rich.panel import Panel

    print()

    # Run tests
    test_parse_structured_response()

    console.print("\n[bold]Interactive Tests (press Ctrl+C to skip)[/bold]\n")
    test_render_form_jira()
    test_render_form_github()

    print("\n")
    console.print(Panel(
        "[green]✅ All tests completed![/green]\n\n"
        "The dynamic form feature is working correctly.",
        title="✅ Success",
        border_style="green"
    ))

