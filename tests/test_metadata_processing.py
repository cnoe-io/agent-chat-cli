#!/usr/bin/env python3
"""
Test if agent-chat-cli properly receives and processes metadata from structured responses.

This test simulates:
1. Agent returning structured response with metadata
2. CLI parsing the JSON
3. CLI displaying fields as questions
4. User providing input
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_chat_cli.chat_interface import render_answer


def test_parse_structured_response_with_metadata():
    """Test parsing a response with execution plan and metadata"""
    
    # Simulate agent response with metadata
    agent_response = json.dumps({
        "execution_plan": {
            "plan_description": "Create GitHub issue with user-provided details",
            "request_type": "Operational",
            "required_agents": ["GitHub"],
            "tasks": [
                {
                    "task_number": 1,
                    "description": "Gather issue details from user",
                    "agent_name": None,
                    "can_parallelize": False
                },
                {
                    "task_number": 2,
                    "description": "Create issue in GitHub repository",
                    "agent_name": "GitHub",
                    "can_parallelize": False
                }
            ],
            "execution_mode": "sequential"
        },
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
                    "field_name": "priority",
                    "field_description": "Issue priority level",
                    "field_values": ["low", "medium", "high", "critical"]
                }
            ]
        }
    })
    
    print("=" * 70)
    print("TEST: Parse Structured Response with Metadata")
    print("=" * 70)
    print()
    
    # Parse the response
    try:
        structured = json.loads(agent_response)
    except json.JSONDecodeError:
        structured = None
    
    if structured is None:
        print("❌ FAILED: Could not parse structured response")
        return False
    
    print("✅ PASSED: Successfully parsed structured response")
    print()
    
    # Check for execution_plan
    if 'execution_plan' in structured:
        plan = structured['execution_plan']
        print("✅ Execution Plan Found:")
        print(f"   Description: {plan.get('plan_description')}")
        print(f"   Agents: {plan.get('required_agents')}")
        print(f"   Tasks: {len(plan.get('tasks', []))}")
    else:
        print("⚠️  No execution plan in response")
    print()
    
    # Check for content
    content = structured.get('content', '')
    if content:
        print(f"✅ Content: {content[:60]}...")
    print()
    
    # Check for metadata
    metadata = structured.get('metadata')
    require_input = structured.get('require_user_input', False)
    
    if not metadata:
        print("❌ FAILED: No metadata found")
        return False
    
    if not require_input:
        print("❌ FAILED: require_user_input not set to True")
        return False
    
    print(f"✅ require_user_input: {require_input}")
    print()
    
    # Check input fields
    input_fields = metadata.get('input_fields', [])
    if not input_fields:
        print("❌ FAILED: No input_fields in metadata")
        return False
    
    print(f"✅ Found {len(input_fields)} input fields:")
    print()
    
    for field in input_fields:
        field_name = field.get('field_name')
        field_desc = field.get('field_description')
        field_values = field.get('field_values')
        
        print(f"   📝 {field_name}")
        print(f"      Description: {field_desc}")
        if field_values:
            print(f"      Options: {', '.join(field_values)}")
            print("      Type: Dropdown")
        else:
            print("      Type: Text input")
        print()
    
    print("=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print()
    
    return True


def test_render_answer_with_metadata():
    """Test that render_answer properly handles structured responses"""
    
    print("=" * 70)
    print("TEST: Render Answer with Metadata")
    print("=" * 70)
    print()
    print("This test displays how the CLI should render the response.")
    print("The actual display will appear below:")
    print("=" * 70)
    print()
    
    # Simulate agent response
    agent_response = json.dumps({
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
                    "field_name": "priority",
                    "field_description": "Issue priority level",
                    "field_values": ["low", "medium", "high", "critical"]
                }
            ]
        }
    })
    
    # This should display styled output with questions
    try:
        render_answer(agent_response, agent_name="AI Platform Engineer")
        print()
        print("=" * 70)
        print("✅ Render completed successfully")
        print("=" * 70)
        return True
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Render failed with error: {e}")
        print("=" * 70)
        return False


def test_metadata_without_execution_plan():
    """Test metadata handling when execution plan is already streamed"""
    
    print()
    print("=" * 70)
    print("TEST: Metadata Without Execution Plan")
    print("=" * 70)
    print()
    print("Testing scenario where execution plan was already streamed")
    print("and only content + metadata remain in final response.")
    print()
    
    # Response without execution_plan (already streamed separately)
    agent_response = json.dumps({
        "content": "To create a Jira ticket, please provide:",
        "is_task_complete": False,
        "require_user_input": True,
        "metadata": {
            "user_input": True,
            "input_fields": [
                {
                    "field_name": "project_key",
                    "field_description": "Jira project key",
                    "field_values": ["CAIPE", "DEVOPS", "PLATFORM"]
                },
                {
                    "field_name": "issue_type",
                    "field_description": "Type of issue",
                    "field_values": ["Bug", "Task", "Story", "Epic"]
                },
                {
                    "field_name": "summary",
                    "field_description": "Brief issue summary",
                    "field_values": None
                }
            ]
        }
    })
    
    try:
        structured = json.loads(agent_response)
    except json.JSONDecodeError:
        structured = None
    
    if structured is None:
        print("❌ FAILED: Could not parse response")
        return False
    
    # Should still work without execution_plan
    if 'content' in structured and 'metadata' in structured:
        print("✅ PASSED: Response parsed correctly without execution_plan")
        print(f"   Content: {structured['content']}")
        print(f"   Input fields: {len(structured['metadata']['input_fields'])}")
        
        # Display it
        print()
        print("Rendering output:")
        print("-" * 70)
        render_answer(agent_response, agent_name="AI Platform Engineer")
        print("-" * 70)
        
        return True
    else:
        print("❌ FAILED: Missing content or metadata")
        return False


def main():
    """Run all metadata processing tests"""
    
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "AGENT-CHAT-CLI METADATA TEST SUITE" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    tests = [
        ("Parse Structured Response", test_parse_structured_response_with_metadata),
        ("Render with Metadata", test_render_answer_with_metadata),
        ("Metadata without Plan", test_metadata_without_execution_plan),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print()
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ TEST CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        print()
    
    # Summary
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 25 + "TEST SUMMARY" + " " * 31 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    print()
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed!")
        return 0
    else:
        print(f"⚠️  {passed}/{total} tests passed, {total - passed} failed")
        return 1


if __name__ == "__main__":
    exit(main())

