"""Tests for A2A client functionality."""

import pytest
from unittest.mock import Mock
from agent_chat_cli.a2a_client import (
    debug_log,
    create_send_message_payload,
    extract_response_text,
    _flatten_text_from_message_dict
)


def test_debug_log():
    """Test debug logging function."""
    # Test that debug_log doesn't crash
    debug_log("test message")
    assert True  # If we get here, the function didn't crash


def test_create_send_message_payload():
    """Test message payload creation."""
    text = "Hello, agent!"
    payload = create_send_message_payload(text)
    
    assert "message" in payload
    assert payload["message"]["role"] == "user"
    assert len(payload["message"]["parts"]) == 1
    assert payload["message"]["parts"][0]["type"] == "text"
    assert payload["message"]["parts"][0]["text"] == text
    assert "messageId" in payload["message"]
    assert "contextId" in payload["message"]


def test_flatten_text_from_message_dict():
    """Test text extraction from message dictionaries."""
    # Test direct text
    message_with_text = {"text": "Hello world"}
    result = _flatten_text_from_message_dict(message_with_text)
    assert result == "Hello world"
    
    # Test parts-based message
    message_with_parts = {
        "parts": [
            {"kind": "text", "text": "Hello "},
            {"kind": "text", "text": "world"}
        ]
    }
    result = _flatten_text_from_message_dict(message_with_parts)
    assert result == "Hello world"
    
    # Test empty message
    empty_message = {}
    result = _flatten_text_from_message_dict(empty_message)
    assert result == ""


def test_extract_response_text():
    """Test response text extraction."""
    # Test with mock response
    mock_response = Mock()
    mock_response.model_dump.return_value = {
        "result": {
            "artifacts": [
                {
                    "parts": [
                        {"kind": "text", "text": "Test response"}
                    ]
                }
            ]
        }
    }
    
    result = extract_response_text(mock_response)
    assert result == "Test response"
    
    # Test with empty response
    empty_response = Mock()
    empty_response.model_dump.return_value = {"result": {}}
    
    result = extract_response_text(empty_response)
    assert result == ""


@pytest.mark.asyncio
async def test_handle_user_input_mock():
    """Test handle_user_input with mocked dependencies."""
    # This is a placeholder test - full testing would require extensive mocking
    # of the A2A client and HTTP connections
    from agent_chat_cli.a2a_client import handle_user_input
    
    # For now, just test that the function exists and can be called
    # In a real test, we'd mock the HTTP client and A2A client
    assert handle_user_input is not None
    
    # TODO: Add comprehensive mocking tests for the full flow

