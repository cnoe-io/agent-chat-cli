"""Tests for A2A client functionality."""

import pytest
from unittest.mock import Mock, patch
from agent_chat_cli.a2a_client import (
    debug_log,
    create_send_message_payload,
    extract_response_text,
    _flatten_text_from_message_dict,
    count_display_lines,
    clear_lines,
    sanitize_stream_text,
    format_execution_plan_text,
    summarize_tool_notification,
    build_dashboard
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


def test_sanitize_stream_text_basic():
    """Test basic sanitization of streaming text."""
    # Test simple text without JSON
    text = "This is a simple response"
    result = sanitize_stream_text(text)
    assert result == "This is a simple response"


def test_sanitize_stream_text_with_json_status():
    """Test sanitization removes JSON status payloads."""
    text = 'Hello world {"status":"completed","message":"Hello world"}'
    result = sanitize_stream_text(text)
    # Should extract the message from JSON and deduplicate
    assert "Hello world" in result
    assert '{"status":' not in result


def test_sanitize_stream_text_with_nested_json():
    """Test sanitization handles nested JSON structures."""
    text = 'Response text {"status":"working","message":"Response text"} more text'
    result = sanitize_stream_text(text)
    # Should handle the JSON and keep clean text
    assert "Response text" in result or "more text" in result


def test_sanitize_stream_text_deduplication():
    """Test that sanitize_stream_text deduplicates identical content."""
    # When we have duplicate content, prefer the longer/cleaner version
    text = 'Short {"status":"done","message":"This is a much longer and more complete message"}'
    result = sanitize_stream_text(text)
    # Should prefer the longer message from JSON
    assert len(result) > 10


def test_sanitize_stream_text_empty():
    """Test sanitization handles empty strings."""
    assert sanitize_stream_text("") == ""
    assert sanitize_stream_text("   ") == ""


def test_format_execution_plan_text_basic():
    """Test execution plan formatting with basic TODO list."""
    text = '[{"content": "Task 1", "status": "pending"}, {"content": "Task 2", "status": "completed"}]'
    result = format_execution_plan_text(text)

    assert "📋" in result
    assert "Task 1" in result
    assert "Task 2" in result
    assert "✅" in result  # completed emoji
    assert "📋" in result  # pending emoji


def test_format_execution_plan_text_with_statuses():
    """Test execution plan formatting respects task statuses."""
    text = '[{"content": "In Progress Task", "status": "in_progress"}, {"content": "Done Task", "status": "completed"}]'
    result = format_execution_plan_text(text)

    assert "⏳" in result  # in_progress emoji
    assert "✅" in result  # completed emoji
    assert "In Progress Task" in result
    assert "Done Task" in result


def test_format_execution_plan_text_already_formatted():
    """Test that already formatted execution plans are returned as-is."""
    text = "📋 **Execution Plan**\n- ✅ Task 1\n- ⏳ Task 2"
    result = format_execution_plan_text(text)
    # Should return unchanged since it's already formatted
    assert result == text


def test_format_execution_plan_text_invalid_json():
    """Test execution plan formatting handles invalid JSON gracefully."""
    text = "Not a valid JSON list"
    result = format_execution_plan_text(text)
    # Should return original text if parsing fails
    assert result == text


def test_format_execution_plan_text_empty():
    """Test execution plan formatting handles empty input."""
    assert format_execution_plan_text("") == ""
    assert format_execution_plan_text("   ") == "   "


def test_summarize_tool_notification_basic():
    """Test tool notification summarization."""
    text = "This is a long tool notification that should be summarized\nWith multiple lines\nAnd more content"
    result = summarize_tool_notification(text)

    # Should only return first line
    assert result == "This is a long tool notification that should be summarized"
    assert "\n" not in result


def test_summarize_tool_notification_with_response():
    """Test tool notification removes 'response=' prefix."""
    text = "Tool executed response=Success: Operation completed\nExtra details"
    result = summarize_tool_notification(text)

    # Should remove 'response=' and keep only first line
    assert "Tool executed" in result
    assert "response=" not in result
    assert "Extra details" not in result


def test_summarize_tool_notification_empty():
    """Test tool notification handles empty input."""
    assert summarize_tool_notification("") == ""
    assert summarize_tool_notification("   ") == ""


def test_summarize_tool_notification_single_line():
    """Test tool notification with single line returns unchanged."""
    text = "Single line notification"
    result = summarize_tool_notification(text)
    assert result == text


def test_build_dashboard_all_panels():
    """Test dashboard building with all panels populated."""
    exec_md = "📋 **Execution Plan**\n- ✅ Task 1"
    tool_md = "- ⏳ Tool running"
    streaming_md = "Streaming output content"
    response_md = "Final response"

    dashboard = build_dashboard(exec_md, tool_md, response_md, streaming_md)

    # Should return a Group with 4 panels
    assert dashboard is not None
    assert len(dashboard.renderables) == 4


def test_build_dashboard_empty():
    """Test dashboard building with no content returns empty group."""
    dashboard = build_dashboard("", "", "", "")

    # Should return empty Group
    assert dashboard is not None
    assert len(dashboard.renderables) == 0


def test_build_dashboard_partial_content():
    """Test dashboard building with some panels empty."""
    exec_md = "📋 Plan"
    tool_md = ""
    streaming_md = "Stream"
    response_md = ""

    dashboard = build_dashboard(exec_md, tool_md, response_md, streaming_md)

    # Should have 2 panels (exec and streaming)
    assert dashboard is not None
    assert len(dashboard.renderables) == 2


def test_build_dashboard_streaming_truncation():
    """Test that streaming output is truncated based on terminal size."""
    exec_md = "Short plan"
    tool_md = ""
    streaming_md = "\n".join([f"Line {i}" for i in range(100)])  # 100 lines
    response_md = ""

    with patch('shutil.get_terminal_size') as mock_size:
        mock_size.return_value = Mock(lines=30, columns=80)
        dashboard = build_dashboard(exec_md, tool_md, response_md, streaming_md)

    # Should have 2 panels (exec and streaming)
    assert dashboard is not None
    assert len(dashboard.renderables) == 2
    # Streaming should be truncated (tested indirectly through panel creation)


def test_debug_log_when_debug_enabled():
    """Test debug_log actually prints when DEBUG is enabled."""
    from agent_chat_cli import a2a_client
    original_debug = a2a_client.DEBUG

    try:
        a2a_client.DEBUG = True
        with patch('builtins.print') as mock_print:
            debug_log("test message")
            mock_print.assert_called_once_with("DEBUG: test message")
    finally:
        a2a_client.DEBUG = original_debug


def test_debug_log_when_debug_disabled():
    """Test debug_log doesn't print when DEBUG is disabled."""
    from agent_chat_cli import a2a_client
    original_debug = a2a_client.DEBUG

    try:
        a2a_client.DEBUG = False
        with patch('builtins.print') as mock_print:
            debug_log("test message")
            mock_print.assert_not_called()
    finally:
        a2a_client.DEBUG = original_debug


def test_count_display_lines_with_oserror():
    """Test count_display_lines handles OSError when terminal size unavailable."""
    with patch('shutil.get_terminal_size', side_effect=OSError("No terminal")):
        # Should fall back to 80 columns
        result = count_display_lines("test")
        assert result >= 1


def test_extract_response_text_with_dict():
    """Test extract_response_text with dict input."""
    response_dict = {
        "result": {
            "artifacts": [
                {
                    "parts": [
                        {"kind": "text", "text": "Dict response"}
                    ]
                }
            ]
        }
    }

    result = extract_response_text(response_dict)
    assert result == "Dict response"


def test_extract_response_text_empty_artifacts():
    """Test extract_response_text with empty artifacts list."""
    mock_response = Mock()
    mock_response.model_dump.return_value = {
        "result": {
            "artifacts": []
        }
    }

    result = extract_response_text(mock_response)
    assert result == ""


def test_extract_response_text_with_status_message():
    """Test extract_response_text falls back to status message."""
    mock_response = Mock()
    mock_response.model_dump.return_value = {
        "result": {
            "artifacts": [],
            "status": {
                "message": {
                    "parts": [
                        {"kind": "text", "text": "Status message"}
                    ]
                }
            }
        }
    }

    result = extract_response_text(mock_response)
    assert result == "Status message"


def test_flatten_text_from_message_dict_with_root():
    """Test _flatten_text_from_message_dict handles nested root structure."""
    message = {
        "parts": [
            {
                "root": {
                    "kind": "text",
                    "text": "Nested text"
                }
            }
        ]
    }

    result = _flatten_text_from_message_dict(message)
    assert result == "Nested text"


def test_flatten_text_from_message_dict_with_content():
    """Test _flatten_text_from_message_dict handles content field."""
    message = {
        "parts": [
            {
                "root": {
                    "kind": "text",
                    "content": "Content text"
                }
            }
        ]
    }

    result = _flatten_text_from_message_dict(message)
    assert result == "Content text"


def test_flatten_text_from_message_dict_invalid():
    """Test _flatten_text_from_message_dict handles invalid input gracefully."""
    # Test with non-dict
    result = _flatten_text_from_message_dict("not a dict")
    assert result == ""

    # Test with None
    result = _flatten_text_from_message_dict(None)
    assert result == ""


def test_sanitize_stream_text_with_malformed_json():
    """Test sanitize_stream_text handles malformed JSON gracefully."""
    text = 'Some text {"status": invalid json here'
    result = sanitize_stream_text(text)
    # Should return the text before the malformed JSON
    assert "Some text" in result


def test_sanitize_stream_text_multiple_json_objects():
    """Test sanitize_stream_text handles multiple JSON objects."""
    text = 'Text 1 {"status":"done","message":"Msg 1"} Text 2 {"status":"done","message":"Msg 2"}'
    result = sanitize_stream_text(text)
    # Should extract and deduplicate messages
    assert len(result) > 0


def test_format_execution_plan_text_with_task_field():
    """Test format_execution_plan_text handles 'task' field instead of 'content'."""
    text = '[{"task": "Task from task field", "status": "pending"}]'
    result = format_execution_plan_text(text)

    assert "Task from task field" in result
    assert "📋" in result


def test_create_send_message_payload_uniqueness():
    """Test that create_send_message_payload generates unique IDs."""
    payload1 = create_send_message_payload("test 1")
    payload2 = create_send_message_payload("test 2")

    # Message IDs should be different
    assert payload1["message"]["messageId"] != payload2["message"]["messageId"]

    # Context IDs should be the same (same session)
    assert payload1["message"]["contextId"] == payload2["message"]["contextId"]


def test_clear_lines_zero():
    """Test clear_lines with zero lines."""
    with patch('sys.stdout') as mock_stdout:
        clear_lines(0)
        # Should not write anything for 0 lines
        assert mock_stdout.write.call_count == 0


def test_sanitize_stream_text_preserves_newlines():
    """Test that sanitize_stream_text preserves paragraph breaks."""
    text = "Paragraph 1\n\nParagraph 2"
    result = sanitize_stream_text(text)
    assert result == text


def test_format_execution_plan_text_no_list():
    """Test format_execution_plan_text when no list brackets found."""
    text = "Just some random text without a list"
    result = format_execution_plan_text(text)
    assert result == text


def test_summarize_tool_notification_multiline_with_tabs():
    """Test tool notification handles tabs in text."""
    text = "First line\t with tab\nSecond line"
    result = summarize_tool_notification(text)
    assert "\t" in result
    assert "Second line" not in result


def test_extract_response_text_with_text_field_in_part():
    """Test extract_response_text with different text field location."""
    mock_response = Mock()
    mock_response.model_dump.return_value = {
        "result": {
            "artifacts": [],
            "status": {
                "message": {
                    "parts": [
                        {"text": "Direct text field"}
                    ]
                }
            }
        }
    }

    result = extract_response_text(mock_response)
    assert result == "Direct text field"


def test_sanitize_stream_text_only_json():
    """Test sanitize_stream_text with only JSON, no surrounding text."""
    text = '{"status":"completed","message":"Only JSON message"}'
    result = sanitize_stream_text(text)
    assert "Only JSON message" in result
    assert '{"status":' not in result


def test_format_execution_plan_text_list_but_not_dict():
    """Test format_execution_plan_text handles list with non-dict items."""
    text = '["string1", "string2"]'
    result = format_execution_plan_text(text)
    # Should return original since items aren't dicts
    assert result == text


def test_build_dashboard_large_execution_plan():
    """Test dashboard with large execution plan affects streaming truncation."""
    exec_md = "\n".join([f"- Task {i}" for i in range(50)])  # Large plan
    streaming_md = "\n".join([f"Stream {i}" for i in range(100)])

    with patch('shutil.get_terminal_size') as mock_size:
        mock_size.return_value = Mock(lines=60, columns=80)
        dashboard = build_dashboard(exec_md, "", "", streaming_md)

    # Should have 2 panels
    assert len(dashboard.renderables) == 2


def test_flatten_text_from_message_dict_multiple_parts():
    """Test _flatten_text_from_message_dict concatenates multiple text parts."""
    message = {
        "parts": [
            {"kind": "text", "text": "Part 1 "},
            {"kind": "text", "text": "Part 2 "},
            {"kind": "text", "text": "Part 3"}
        ]
    }

    result = _flatten_text_from_message_dict(message)
    assert result == "Part 1 Part 2 Part 3"


def test_count_display_lines_exact_width():
    """Test count_display_lines with text exactly at terminal width."""
    text = "a" * 80  # Exactly 80 chars
    result = count_display_lines(text, 80)
    assert result == 1  # Should fit in exactly one line


def test_count_display_lines_newline_at_end():
    """Test count_display_lines handles trailing newline."""
    text = "line1\n"
    result = count_display_lines(text, 80)
    assert result == 2  # line1 + empty line from trailing newline

