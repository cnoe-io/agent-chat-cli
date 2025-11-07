"""Test case that should FAIL - demonstrates what happens without UserInputMetaData prefix"""

import pytest
from agent_chat_cli.a2a_client import parse_structured_response


def test_plain_text_should_not_trigger_metadata_form():
    """
    This test demonstrates that plain text responses (like the GitHub issue example)
    do NOT trigger the metadata form. This is the current problem.
    
    The agent is responding with:
    "To create a GitHub issue, I need the following information: ..."
    
    But it should respond with:
    "UserInputMetaData: {...}"
    
    This test will PASS because our code correctly doesn't trigger metadata
    for plain text. But it shows the agent isn't using the new format.
    """
    response = """To create a GitHub issue, I need the following information:

1. Title: A brief summary of the issue.
2. Description: Detailed information about the issue.
3. Labels: Any labels you want to assign.
4. Assignee: The GitHub username (optional).
5. Repository: The name of the repository.

Please provide these details so I can proceed with creating the issue."""
    
    result = parse_structured_response(response)
    
    # This will PASS - correctly identifies it as plain text
    assert result["require_user_input"] is False
    assert result["metadata"] is None
    
    # But this is NOT what we want! We want the agent to use UserInputMetaData format
    # This test documents the current problem


@pytest.mark.xfail(reason="Agent not yet using UserInputMetaData format - this is the expected behavior we want")
def test_agent_should_use_userinputmetadata_format():
    """
    This test will FAIL because the agent is not yet using the UserInputMetaData format.
    This is marked as xfail to document what we expect in the future.
    
    When the agent is properly prompted to use UserInputMetaData format,
    this test should pass.
    """
    # Simulate what the agent SHOULD respond with
    expected_response = '''UserInputMetaData: {
  "require_user_input": true,
  "content": "To create a GitHub issue, I need the following information:",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "name": "title",
        "description": "A brief summary of the issue",
        "type": "text",
        "required": true
      },
      {
        "name": "description",
        "description": "Detailed information about the issue",
        "type": "textarea",
        "required": true
      },
      {
        "name": "labels",
        "description": "Labels to assign (comma-separated)",
        "type": "text",
        "required": false
      },
      {
        "name": "assignee",
        "description": "GitHub username of assignee",
        "type": "text",
        "required": false
      },
      {
        "name": "repository",
        "description": "Repository name (owner/repo)",
        "type": "text",
        "required": true
      }
    ]
  }
}'''
    
    # But the agent is currently responding with plain text instead
    actual_agent_response = """To create a GitHub issue, I need the following information:

1. Title: A brief summary of the issue.
2. Description: Detailed information about the issue.
3. Labels: Any labels you want to assign.
4. Assignee: The GitHub username (optional).
5. Repository: The name of the repository.

Please provide these details so I can proceed with creating the issue."""
    
    # Parse both
    expected_result = parse_structured_response(expected_response)
    actual_result = parse_structured_response(actual_agent_response)
    
    # This assertion will FAIL because actual_result doesn't have metadata
    assert actual_result["require_user_input"] == expected_result["require_user_input"]
    assert actual_result["metadata"] is not None
    assert len(actual_result["metadata"]["input_fields"]) == 5


def test_demonstrate_working_format():
    """
    This test PASSES - demonstrates that our parsing code works correctly
    when the agent uses the UserInputMetaData format.
    
    The issue is that the agent needs to be prompted to use this format.
    """
    correct_format = '''UserInputMetaData: {
  "require_user_input": true,
  "content": "To create a GitHub issue, I need the following information:",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "name": "title",
        "description": "Issue title",
        "type": "text",
        "required": true
      }
    ]
  }
}'''
    
    result = parse_structured_response(correct_format)
    
    # This will PASS - our code works correctly
    assert result["require_user_input"] is True
    assert result["metadata"] is not None
    assert len(result["metadata"]["input_fields"]) == 1


