"""Test UserInputMetaData prefix parsing"""

import pytest
from agent_chat_cli.a2a_client import parse_structured_response


def test_user_input_metadata_prefix_format():
    """Test parsing UserInputMetaData: prefix format"""
    response = '''UserInputMetaData: {
  "require_user_input": true,
  "content": "To create a GitHub pull request, I need the following information:",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "name": "branch_name",
        "description": "The source branch for the pull request",
        "type": "text",
        "required": true
      },
      {
        "name": "pr_title",
        "description": "Title of the pull request",
        "type": "text",
        "required": true
      }
    ]
  }
}'''
    
    result = parse_structured_response(response)
    
    assert result["require_user_input"] is True
    assert result["content"] == "To create a GitHub pull request, I need the following information:"
    assert result["metadata"] is not None
    assert "input_fields" in result["metadata"]
    assert len(result["metadata"]["input_fields"]) == 2
    assert result["metadata"]["input_fields"][0]["name"] == "branch_name"
    assert result["metadata"]["input_fields"][1]["name"] == "pr_title"


def test_legacy_json_format():
    """Test parsing legacy JSON format (no prefix)"""
    response = '''{
  "require_user_input": true,
  "content": "Please provide details",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "name": "test_field",
        "description": "Test field description",
        "type": "text",
        "required": true
      }
    ]
  }
}'''
    
    result = parse_structured_response(response)
    
    assert result["require_user_input"] is True
    assert result["content"] == "Please provide details"
    assert result["metadata"] is not None
    assert len(result["metadata"]["input_fields"]) == 1


def test_regular_text_no_json():
    """Test parsing regular text (no JSON)"""
    response = "Here is the ArgoCD version: v2.8.0"
    
    result = parse_structured_response(response)
    
    assert result["require_user_input"] is False
    assert result["content"] == "Here is the ArgoCD version: v2.8.0"
    assert result["metadata"] is None


def test_user_input_metadata_with_select_field():
    """Test parsing UserInputMetaData with select field type"""
    response = '''UserInputMetaData: {
  "require_user_input": true,
  "content": "Please select an option:",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "name": "priority",
        "description": "Issue priority level",
        "type": "select",
        "required": true,
        "options": ["Critical", "High", "Medium", "Low"]
      }
    ]
  }
}'''
    
    result = parse_structured_response(response)
    
    assert result["require_user_input"] is True
    assert result["metadata"]["input_fields"][0]["type"] == "select"
    assert result["metadata"]["input_fields"][0]["options"] == ["Critical", "High", "Medium", "Low"]


def test_user_input_metadata_invalid_json():
    """Test handling of invalid JSON after UserInputMetaData prefix"""
    response = 'UserInputMetaData: { invalid json }'
    
    result = parse_structured_response(response)
    
    # Should fall back to treating as regular text
    assert result["require_user_input"] is False
    assert result["content"] == response
    assert result["metadata"] is None


def test_empty_response():
    """Test handling of empty response"""
    result = parse_structured_response("")
    
    assert result["require_user_input"] is False
    assert result["content"] == ""
    assert result["metadata"] is None


def test_user_input_metadata_multiple_fields():
    """Test parsing UserInputMetaData with multiple field types"""
    response = '''UserInputMetaData: {
  "require_user_input": true,
  "content": "Create a Jira issue:",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "name": "title",
        "description": "Issue title",
        "type": "text",
        "required": true
      },
      {
        "name": "description",
        "description": "Detailed description",
        "type": "textarea",
        "required": true
      },
      {
        "name": "priority",
        "description": "Priority level",
        "type": "select",
        "required": true,
        "options": ["High", "Medium", "Low"]
      },
      {
        "name": "estimate",
        "description": "Story points",
        "type": "number",
        "required": false
      },
      {
        "name": "urgent",
        "description": "Mark as urgent",
        "type": "boolean",
        "required": false
      }
    ]
  }
}'''
    
    result = parse_structured_response(response)
    
    assert result["require_user_input"] is True
    assert len(result["metadata"]["input_fields"]) == 5
    
    # Verify each field type
    fields = {f["name"]: f for f in result["metadata"]["input_fields"]}
    assert fields["title"]["type"] == "text"
    assert fields["description"]["type"] == "textarea"
    assert fields["priority"]["type"] == "select"
    assert fields["estimate"]["type"] == "number"
    assert fields["urgent"]["type"] == "boolean"


