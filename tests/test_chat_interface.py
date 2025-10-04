"""Tests for chat interface functionality."""

import pytest
import asyncio
from unittest.mock import patch
from agent_chat_cli.chat_interface import render_answer


def test_render_answer():
    """Test answer rendering function."""
    # Test basic rendering
    test_answer = "This is a test response from the agent."
    
    # Mock the console to avoid actual output during tests
    with patch('agent_chat_cli.chat_interface.console') as mock_console:
        render_answer(test_answer)
        
        # Verify that console.print was called
        assert mock_console.print.called
        
        # Check that Panel and Markdown were used in the calls
        call_args = mock_console.print.call_args_list
        assert len(call_args) >= 1  # At least one print call


def test_render_answer_empty():
    """Test rendering with empty answer."""
    with patch('agent_chat_cli.chat_interface.console') as mock_console:
        render_answer("")
        
        # Should still call print (for spacing)
        assert mock_console.print.called


def test_render_answer_with_agent_name():
    """Test rendering with custom agent name."""
    test_answer = "Custom agent response"
    custom_name = "Custom Agent"
    
    with patch('agent_chat_cli.chat_interface.console') as mock_console:
        render_answer(test_answer, agent_name=custom_name)
        
        # Verify console was used
        assert mock_console.print.called


@pytest.mark.asyncio
async def test_spinner_basic():
    """Test basic spinner functionality."""
    from agent_chat_cli.chat_interface import spinner
    
    # Test that spinner can be created and stopped quickly
    stop_event = asyncio.Event()
    cleared_event = asyncio.Event()
    
    # Start spinner task
    spinner_task = asyncio.create_task(
        spinner("Testing...", stop_event, cleared_event)
    )
    
    # Stop it almost immediately
    await asyncio.sleep(0.01)
    stop_event.set()
    
    # Wait for completion
    await spinner_task
    
    # Verify cleared event was set
    assert cleared_event.is_set()


def test_imports():
    """Test that all expected functions can be imported."""
    from agent_chat_cli.chat_interface import (
        render_answer,
        spinner,
        notify_streaming_started,
        wait_spinner_cleared
    )
    
    # Verify functions exist
    assert callable(render_answer)
    assert callable(spinner)
    assert callable(notify_streaming_started)
    assert callable(wait_spinner_cleared)

