"""Tests for A2A client functionality."""

import pytest
from unittest.mock import Mock, patch
from agent_chat_cli.a2a_client import (
    debug_log,
    create_send_message_payload,
    extract_response_text,
    _flatten_text_from_message_dict,
    count_display_lines,
    clear_lines
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


def test_count_display_lines():
    """Test line counting for terminal display."""
    # Test simple single line
    assert count_display_lines("hello", 80) == 1
    
    # Test empty string
    assert count_display_lines("", 80) == 0
    
    # Test multiline string
    text = "line1\nline2\nline3"
    assert count_display_lines(text, 80) == 3
    
    # Test line wrapping
    long_line = "a" * 160  # 160 chars should wrap to 2 lines with width 80
    assert count_display_lines(long_line, 80) == 2
    
    # Test with default terminal width (should not crash)
    result = count_display_lines("test")
    assert result >= 1


def test_clear_lines():
    """Test terminal line clearing functionality."""
    # Mock stdout to capture the escape codes
    with patch('sys.stdout') as mock_stdout:
        clear_lines(3)
        
        # Verify write was called multiple times for escape sequences
        assert mock_stdout.write.called
        assert mock_stdout.flush.called
        
        # Check that escape sequences for cursor movement were written
        write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert any('\033[1A' in call for call in write_calls)  # Move cursor up
        assert any('\033[2K' in call for call in write_calls)  # Clear line


def test_clear_lines_safety_limit():
    """Test that clear_lines respects safety limits."""
    with patch('sys.stdout') as mock_stdout:
        # Test that clearing more than 100 lines is capped
        clear_lines(200)
        
        # Count the number of cursor-up movements (should be max 100)
        write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        cursor_up_calls = [call for call in write_calls if '\033[1A' in call]
        assert len(cursor_up_calls) <= 100


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

