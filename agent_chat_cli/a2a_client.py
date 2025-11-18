# Copyright CNOE Contributors (https://cnoe.io)
# SPDX-License-Identifier: Apache-2.0

"""
A2A (Agent-to-Agent) Client for Interactive Chat Interface

This module provides a comprehensive client implementation for communicating with A2A agents
through both streaming and non-streaming protocols. It features:

- Real-time streaming responses with visual feedback (ASCII spinner)
- Beautiful markdown rendering of agent responses
- Support for multiple streaming event types (Task, TaskArtifactUpdateEvent, TaskStatusUpdateEvent)
- Graceful fallback from streaming to non-streaming mode
- Comprehensive error handling and debugging capabilities
- Rich console interface with panels and formatting

Key Components:
- Agent card discovery and authentication
- Streaming message handling with real-time display
- Response text extraction from various event types
- Visual feedback through animated spinners and formatted panels

Environment Variables:
- A2A_HOST: Agent host (default: localhost)
- A2A_PORT: Agent port (default: 8000)
- A2A_TLS: Enable TLS (default: false)
- A2A_TOKEN: Authentication token (optional)
- A2A_DEBUG_CLIENT: Enable debug logging (default: false)
"""

import os
import asyncio
import logging
import sys
import shutil
import json
import ast
from uuid import uuid4
from typing import Any, Optional, List

from pydantic import BaseModel, Field
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.table import Table
from agent_chat_cli.chat_interface import run_chat_loop, render_answer, notify_streaming_started, wait_spinner_cleared

import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
  SendMessageResponse,
  SendMessageSuccessResponse,
  SendMessageRequest,
  MessageSendParams,
  AgentCard,
  SendStreamingMessageRequest,
)
from a2a.types import TaskState
import warnings

# Suppress protobuf version warnings
warnings.filterwarnings(
  "ignore",
  message="Protobuf gencode version .* is exactly one major version older than the runtime version .*",
  category=UserWarning,
  module="google.protobuf.runtime_version"
)

# Set a2a.client logging to WARNING
logging.getLogger("a2a.client").setLevel(logging.WARNING)

PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
EXTENDED_AGENT_CARD_PATH = '/agent/authenticatedExtendedCard'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("a2a_client")

warnings.filterwarnings(
  "ignore",
  message=".*`dict` method is deprecated.*",
  category=DeprecationWarning,
  module=".*"
)

AGENT_HOST = os.environ.get("A2A_HOST", "localhost")
AGENT_PORT = os.environ.get("A2A_PORT", "8000")
if os.environ.get("A2A_TLS", "false").lower() in ["1", "true", "yes"]:
  AGENT_URL = f"https://{AGENT_HOST}:{AGENT_PORT}"
else:
  AGENT_URL = f"http://{AGENT_HOST}:{AGENT_PORT}"
DEBUG = os.environ.get("A2A_DEBUG_CLIENT", "false").lower() in ["1", "true", "yes"]
if DEBUG:
  logger.debug(f"====== DEBUG MODE - Agent URL: {AGENT_URL} ======")

console = Console()

SESSION_CONTEXT_ID = uuid4().hex


# Pydantic models for structured responses (matching backend schemas)
class InputField(BaseModel):
    """Input field metadata for dynamic forms"""
    field_name: str = Field(description="Field name")
    field_description: str = Field(description="Field description")
    field_values: Optional[List[str]] = Field(default=None, description="Dropdown options")


class Metadata(BaseModel):
    """Response metadata"""
    user_input: bool = Field(description="Whether user input is required")
    input_fields: Optional[List[InputField]] = Field(default=None, description="Input fields for forms")


class PlatformEngineerResponse(BaseModel):
    """Platform Engineer structured response"""
    is_task_complete: bool = Field(description="Whether task is complete")
    require_user_input: bool = Field(description="Whether user input is required")
    content: str = Field(description="Response content")
    metadata: Optional[Metadata] = Field(default=None, description="Metadata for forms")


class JarvisResponse(BaseModel):
    """Jarvis agent structured response"""
    answer: str = Field(description="Response answer")
    metadata: Metadata = Field(description="Metadata for forms")


def debug_log(message: str) -> None:
  """
  Log debug messages when debug mode is enabled.

  Args:
    message: The debug message to log
  """
  if DEBUG:
    print(f"DEBUG: {message}")

def count_display_lines(text: str, terminal_width: int = None) -> int:
  """
  Count the number of terminal lines that text will occupy when displayed.

  Args:
    text: The text to measure
    terminal_width: Terminal width (auto-detected if None)

  Returns:
    Number of lines the text will occupy
  """
  if not text:
    return 0

  if terminal_width is None:
    try:
      terminal_width = shutil.get_terminal_size().columns
    except OSError:
      terminal_width = 80  # Fallback width

  lines = text.split('\n')
  total_lines = 0

  for line in lines:
    if len(line) == 0:
      total_lines += 1
    else:
      # Account for line wrapping
      total_lines += (len(line) + terminal_width - 1) // terminal_width

  return total_lines

def clear_lines(num_lines: int) -> None:
  """
  Clear the specified number of lines from the terminal by moving cursor up and clearing.

  Args:
    num_lines: Number of lines to clear
  """
  if num_lines > 0:
    # Safety: Don't try to clear more than 100 lines (reasonable limit)
    safe_lines = min(num_lines, 100)

    # Move cursor up and clear each line
    for i in range(safe_lines):
      sys.stdout.write('\033[1A')  # Move cursor up one line
      sys.stdout.write('\033[2K')  # Clear entire line

    # Position cursor at beginning of current line and flush
    sys.stdout.write('\r')
    sys.stdout.flush()

def format_execution_plan_text(raw_text: str) -> str:
  """Format execution plan text into a user-friendly markdown checklist."""
  if not raw_text:
    return raw_text

  # If it already contains bullet emojis, assume it's formatted
  stripped = raw_text.strip()
  if stripped.startswith('- ✅') or stripped.startswith('✅') or '📋' in stripped:
    return raw_text

  heading = "📋 **Execution Plan**"
  if 'Updated' in raw_text and 'todo list' in raw_text:
    heading = "📋 **Execution Plan (updated)**"

  list_start = raw_text.find('[')
  list_end = raw_text.rfind(']')
  if list_start == -1 or list_end == -1 or list_end <= list_start:
    return raw_text

  list_segment = raw_text[list_start:list_end + 1]

  try:
    todos = ast.literal_eval(list_segment)
    if not isinstance(todos, list):
      return raw_text
  except Exception:
    return raw_text

  status_emoji = {
    'in_progress': '⏳',
    'completed': '✅',
    'pending': '📋',
  }

  lines = [heading, ""]
  for item in todos:
    if not isinstance(item, dict):
      continue
    content = item.get('content') or item.get('task') or "(no description)"
    status = (item.get('status') or '').lower()
    emoji = status_emoji.get(status, '•')
    lines.append(f"- {emoji} {content}")

  if len(lines) <= 2:
    return raw_text

  return "\n".join(lines)


def summarize_tool_notification(raw_text: str) -> str:
  if not raw_text:
    return ""

  text = raw_text.strip()
  if "response=" in text:
    text = text.split("response=", 1)[0].strip()

  # Safely get first line, handle empty text
  lines = text.splitlines()
  if lines:
    text = lines[0].strip()
  else:
    return ""  # Return empty string if no content

  max_len = 160
  if len(text) > max_len:
    text = text[:max_len].rstrip() + "…"

  return text


def parse_structured_response(text: str) -> dict:
  """
  Parse structured JSON response from agent using Pydantic models.
  Returns dict with: content, require_user_input, metadata

  Supports multiple formats:
  1. UserInputMetaData: {...} - Explicit prefix format
  2. Pure JSON: PlatformEngineerResponse or JarvisResponse
  3. Mixed text + embedded JSON - strips JSON and returns clean text
  """
  if not text or not text.strip():
    return {"content": text, "require_user_input": False, "metadata": None}

  # Check for UserInputMetaData: prefix first
  user_input_metadata_prefix = 'UserInputMetaData:'
  if text.strip().startswith(user_input_metadata_prefix):
    debug_log("🎨 UserInputMetaData prefix detected")
    try:
      # Extract JSON after the prefix
      json_str = text.strip()[len(user_input_metadata_prefix):].strip()
      # Try Pydantic validation first
      try:
        response = PlatformEngineerResponse.model_validate_json(json_str)
        debug_log("✅ UserInputMetaData parsed with Pydantic")
        return {
          "content": response.content,
          "require_user_input": response.require_user_input,
          "metadata": response.metadata.model_dump() if response.metadata else None
        }
      except Exception:
        # Fall back to legacy JSON parsing if Pydantic validation fails
        data = json.loads(json_str)
        if "content" in data:
          debug_log("✅ UserInputMetaData parsed with legacy format")
          return {
            "content": data.get("content", text),
            "require_user_input": data.get("require_user_input", False),
            "metadata": data.get("metadata")
          }
    except Exception as e:
      debug_log(f"❌ Failed to parse UserInputMetaData: {e}")
      # Fall through to try other formats

  # Try pure JSON parsing with Pydantic models
  try:
    data = json.loads(text.strip())

    # Try PlatformEngineerResponse
    try:
      response = PlatformEngineerResponse.model_validate(data)
      debug_log("✅ PlatformEngineerResponse validated with Pydantic")
      return {
        "content": response.content,
        "require_user_input": response.require_user_input,
        "metadata": response.metadata.model_dump() if response.metadata else None
      }
    except Exception:
      pass

    # Try JarvisResponse
    try:
      response = JarvisResponse.model_validate(data)
      debug_log("✅ JarvisResponse validated with Pydantic - converting to standard format")
      return {
        "content": response.answer,
        "require_user_input": True,
        "metadata": response.metadata.model_dump()
      }
    except Exception:
      pass

    # Legacy format without Pydantic validation
    if "content" in data:
      return {
        "content": data.get("content", text),
        "require_user_input": data.get("require_user_input", False),
        "metadata": data.get("metadata")
      }

  except (json.JSONDecodeError, ValueError):
    pass

  # Text with embedded JSON - strip all JSON and return clean text
  debug_log("🧹 Attempting to strip embedded JSON from mixed text")
  clean_text = _strip_embedded_json(text)

  return {"content": clean_text, "require_user_input": False, "metadata": None}


def _strip_embedded_json(text: str) -> str:
  """
  Helper function to strip embedded JSON from mixed text.

  Args:
    text: Text potentially containing embedded JSON

  Returns:
    Clean text with JSON removed
  """
  clean_text = text
  cleaned_parts = []

  # Look for JSON patterns and strip them
  json_patterns = [
    '{"status":',
    '{"answer":',
    '{"is_task_complete":',
    '{"action_taken":',
    '{"formatted_text":',  # format_markdown tool output
    'response='
  ]

  for pattern in json_patterns:
    if pattern in clean_text:
      debug_log(f"🧹 Found pattern '{pattern}' - stripping JSON")
      parts = clean_text.split(pattern, 1)  # Split only once

      if len(parts) > 0:
        # Keep text before JSON
        before_json = parts[0].strip()
        if before_json:
          cleaned_parts.append(before_json)

        # Try to find end of JSON and keep text after
        if len(parts) > 1:
          # Find closing brace using brace counting
          brace_count = 1
          end_idx = 0
          for i, char in enumerate(parts[1]):
            if char == '{':
              brace_count += 1
            elif char == '}':
              brace_count -= 1
              if brace_count == 0:
                end_idx = i + 1
                break

          # Keep text after JSON
          if end_idx > 0 and end_idx < len(parts[1]):
            after_json = parts[1][end_idx:].strip()
            if after_json:
              cleaned_parts.append(after_json)

        clean_text = '\n\n'.join(cleaned_parts) if cleaned_parts else parts[0].strip()
        break

  return clean_text


# Public alias for backward compatibility with tests
def clean_mixed_agent_content(text: str) -> str:
  """
  Public function to clean mixed agent content (text with embedded JSON).
  
  This is an alias for _strip_embedded_json for use in tests and external code.
  
  Args:
    text: Text potentially containing embedded JSON
    
  Returns:
    Clean text with JSON removed
  """
  return _strip_embedded_json(text)


def render_metadata_form(metadata: dict, console: Console = None) -> dict:
  """
  Render an interactive form for metadata input fields using rich prompts.
  Returns dict of field_name -> user_value
  """
  if console is None:
    console = Console()

  if not metadata or not metadata.get("input_fields"):
    return {}

  console.print()
  console.print(Panel(
    "[bold cyan]📋 Input Required[/bold cyan]",
    style="cyan",
    border_style="cyan"
  ))

  input_fields = metadata.get("input_fields", [])
  form_data = {}

  for field in input_fields:
    field_name = field.get("field_name") or field.get("name")
    field_description = field.get("field_description") or field.get("description", "")
    field_values = field.get("field_values") or field.get("options")

    if not field_name:
      continue

    # Display field description if available
    if field_description:
      console.print(f"\n[yellow]{field_description}[/yellow]")

    # Handle different field types
    if field_values and isinstance(field_values, list):
      # Choice field - show options and validate
      console.print(f"[dim]Options: {', '.join(str(v) for v in field_values)}[/dim]")

      while True:
        value = Prompt.ask(
          f"[bold]{field_name}[/bold]",
          default=str(field_values[0]) if field_values else None
        )

        # Validate choice
        if value in [str(v) for v in field_values]:
          form_data[field_name] = value
          break
        else:
          console.print(f"[red]❌ Invalid choice. Please select from: {', '.join(str(v) for v in field_values)}[/red]")

    else:
      # Text field
      value = Prompt.ask(f"[bold]{field_name}[/bold]")
      form_data[field_name] = value

  # Show summary
  console.print()
  table = Table(title="📝 Your Input", show_header=True, header_style="bold cyan")
  table.add_column("Field", style="cyan")
  table.add_column("Value", style="green")

  for field_name, value in form_data.items():
    table.add_row(field_name, str(value))

  console.print(table)
  console.print()

  # Confirm submission
  if not Confirm.ask("[bold]Submit this information?[/bold]", default=True):
    console.print("[yellow]Input cancelled. You can try again.[/yellow]")
    return {}

  return form_data


def sanitize_stream_text(raw_text: str) -> str:
  """Remove status payloads and extract meaningful streaming text."""
  if not raw_text:
    return ""

  text = raw_text.replace("\r", "")

  # Try direct JSON decode first
  try:
    data = json.loads(text)
    if isinstance(data, dict):
      message = data.get("message") or data.get("text")
      if isinstance(message, str):
        return message.strip()
  except (json.JSONDecodeError, TypeError):
    pass

  cleaned_parts: list[str] = []
  remaining = text

  while '{"status":' in remaining:
    before, after = remaining.split('{"status":', 1)
    if before.strip():
      cleaned_parts.append(before.strip())

    # Find the matching closing brace for the JSON object
    brace_count = 1
    brace_index = -1
    for i, char in enumerate(after):
      if char == '{':
        brace_count += 1
      elif char == '}':
        brace_count -= 1
        if brace_count == 0:
          brace_index = i
          break

    if brace_index == -1:
      # No matching brace, remaining text is not valid JSON
      if remaining.strip() and remaining.strip() != text.strip():
        cleaned_parts.append(remaining.strip())
      break

    json_candidate = '{"status":' + after[:brace_index + 1]
    trailing = after[brace_index + 1:]

    try:
      payload = json.loads(json_candidate)
      message = payload.get("message") if isinstance(payload, dict) else None
      if isinstance(message, str) and message.strip():
        # The message might have escaped newlines, convert them
        clean_message = message.replace('\\n', '\n').strip()
        if clean_message:
          cleaned_parts.append(clean_message)
    except json.JSONDecodeError:
      # If JSON parsing fails, just keep the before part
      pass

    remaining = trailing

  if remaining.strip():
    cleaned_parts.append(remaining.strip())

  if not cleaned_parts:
    return text.strip()

  # Deduplicate consecutive identical sections
  deduped: list[str] = []
  for part in cleaned_parts:
    if not deduped or part != deduped[-1]:
      deduped.append(part)

  # Use first non-duplicate part if we have both text and JSON message
  # (they're often duplicates, prefer the cleaner JSON message version)
  if len(deduped) >= 2:
    # If we have the same content with/without JSON formatting, prefer the formatted one
    return deduped[-1] if len(deduped[-1]) >= len(deduped[0]) else deduped[0]

  return "\n\n".join(deduped).strip()


def build_dashboard(execution_md: str, tool_md: str, response_md: str, streaming_md: str = "") -> Group:
  panels = []

  # Get terminal height to calculate available space
  try:
    terminal_height = shutil.get_terminal_size().lines
  except OSError:
    terminal_height = 24  # Fallback to standard terminal height

  # Reserve space for panel borders and padding (rough estimate)
  PANEL_OVERHEAD_PER_PANEL = 4  # 2 for border + 2 for padding
  reserved_lines = 0

  if execution_md:
    exec_lines = len(execution_md.split('\n'))
    reserved_lines += exec_lines + PANEL_OVERHEAD_PER_PANEL
    panels.append(Panel(
      Markdown(execution_md),
      title="🎯 Execution Plan",
      border_style="cyan",
      padding=(1, 2),
    ))

  if tool_md:
    tool_lines = len(tool_md.split('\n'))
    reserved_lines += tool_lines + PANEL_OVERHEAD_PER_PANEL
    panels.append(Panel(
      Markdown(tool_md),
      title="🔧 Tool Activity",
      border_style="magenta",
      padding=(1, 2),
    ))

  if streaming_md:
    # Calculate max lines for streaming output based on remaining screen space
    available_lines = terminal_height - reserved_lines - PANEL_OVERHEAD_PER_PANEL - 5  # 5 for buffer
    max_streaming_lines = max(5, available_lines)  # At least 5 lines

    streaming_lines = streaming_md.split('\n')

    # Debug: log the calculation
    if DEBUG:
      debug_log(f"Terminal height: {terminal_height}, Reserved: {reserved_lines}, Max streaming: {max_streaming_lines}, Actual lines: {len(streaming_lines)}")

    if len(streaming_lines) > max_streaming_lines:
      truncated_md = "...\n\n" + "\n".join(streaming_lines[-max_streaming_lines:])
    else:
      truncated_md = streaming_md

    panels.append(Panel(
      Text(truncated_md),
      title="📝 Streaming Output",
      border_style="yellow",
      padding=(1, 2),
    ))

  if response_md:
    panels.append(Panel(
      Markdown(response_md),
      title="🤖 AI Platform Engineer Response",
      border_style="green",
      padding=(1, 2),
    ))

  # Don't show anything if no panels - cleaner UX
  if not panels:
    # Return empty group - the "⏳ Waiting for agent..." message already appears above
    return Group()

  return Group(*panels)

def create_send_message_payload(text: str) -> dict[str, Any]:
  """
  Create a properly formatted message payload for A2A communication.

  This function constructs the message structure required by the A2A protocol,
  including user role, text content, unique message ID, and session context.

  Args:
    text: The user's input text to send to the agent

  Returns:
    A dictionary containing the formatted message payload with:
    - message.role: Set to "user"
    - message.parts: List containing the text content
    - message.messageId: Unique identifier for this message
    - message.contextId: Session context ID for conversation continuity
  """
  return {
    "message": {
      "role": "user",
      "parts": [
        {"type": "text", "text": text}
      ],
      "messageId": uuid4().hex,
      "contextId": SESSION_CONTEXT_ID  # Include the session context ID in each message
    }
  }

def extract_response_text(response) -> str:
  """
  Extract text content from A2A response objects (non-streaming mode).

  This function handles various response formats and attempts to extract
  meaningful text content from different parts of the response structure.
  It supports both artifacts and status message formats, including DataPart
  for structured JSON responses.

  Args:
    response: The A2A response object (can be Pydantic model, dict, etc.)

  Returns:
    Extracted text content as a string, or empty string if no text found

  Note:
    This function is primarily used for non-streaming responses.
    For streaming responses, use _flatten_text_from_message_dict instead.
  """
  try:
    # Convert response to dictionary format
    if hasattr(response, "model_dump"):
      response_data = response.model_dump()
    elif hasattr(response, "dict"):
      response_data = response.dict()
    elif isinstance(response, dict):
      response_data = response
    else:
      raise ValueError("Unsupported response type")

    result = response_data.get("result", {})

    # Try to extract from artifacts first
    artifacts = result.get("artifacts")
    if artifacts and isinstance(artifacts, list) and len(artifacts) > 0:
      first_artifact = artifacts[0]
      if isinstance(first_artifact, dict) and first_artifact.get("parts"):
        for part in first_artifact["parts"]:
          # Handle TextPart
          if part.get("kind") == "text":
            return part.get("text", "").strip()
          # Handle DataPart (structured JSON like JarvisResponse)
          elif part.get("kind") == "data" and part.get("data"):
            debug_log("📦 DataPart detected in artifact - converting to JSON string")
            return json.dumps(part.get("data"))

    # Fallback to status message
    message = result.get("status", {}).get("message", {})
    for part in message.get("parts", []):
      # Handle TextPart
      if part.get("kind") == "text":
        return part.get("text", "").strip()
      # Handle DataPart
      elif part.get("kind") == "data" and part.get("data"):
        debug_log("📦 DataPart detected in status message - converting to JSON string")
        return json.dumps(part.get("data"))
      # Legacy format
      elif "text" in part:
        return part["text"].strip()

  except Exception as e:
    debug_log(f"Error extracting text: {str(e)}")

  return ""

def _flatten_text_from_message_dict(message: Any) -> str:
  """
  Extract and concatenate text content from message objects (streaming mode).

  This function handles various message formats commonly found in streaming responses:
  - Direct text fields: {text: "content"}
  - Parts-based messages: {parts: [{kind: 'text', text: 'content'}]}
  - Nested root structures: {parts: [{root: {kind: 'text', text: 'content'}}]}

  Args:
    message: Message object or dictionary containing text content

  Returns:
    Concatenated text content from all text parts, or empty string if none found

  Note:
    This function is designed for streaming message processing where text
    may be split across multiple parts or nested in various structures.
  """
  try:
    # Convert message to dictionary format
    if hasattr(message, "model_dump"):
      message = message.model_dump()
    elif hasattr(message, "dict"):
      message = message.dict()

    if not isinstance(message, dict):
      return ""

    # Direct text on message
    if isinstance(message.get("text"), str):
      return message["text"]

    # Parts-based text extraction
    parts = message.get("parts", [])
    if not isinstance(parts, list):
      return ""

    texts: list[str] = []
    for p in parts:
      if not isinstance(p, dict):
        continue

      # Handle nested root payload (e.g., {'root': {'kind': 'text', 'text': '...'}})
      root = p.get("root")
      if isinstance(root, dict):
        kind = root.get("kind") or root.get("type")
        if kind == "text":
          if isinstance(root.get("text"), str):
            texts.append(root["text"])
          elif isinstance(root.get("content"), str):
            texts.append(root["content"])
        continue

      # Flat part payload
      kind = p.get("kind") or p.get("type")
      if kind == "text":
        if isinstance(p.get("text"), str):
          texts.append(p["text"])
        elif isinstance(p.get("content"), str):
          texts.append(p["content"])
    return "".join(texts)
  except Exception:
    return ""



async def handle_user_input(user_input: str, token: str = None) -> None:
  """
  Handle user input by sending it to the A2A agent and displaying the response.

  This is the main function that orchestrates the entire communication flow:
  1. Establishes connection to the A2A agent
  2. Attempts streaming communication first (with real-time display)
  3. Falls back to non-streaming mode if streaming fails
  4. Displays responses in beautiful markdown panels
  5. Provides visual feedback through animated spinners

  The function supports both streaming and non-streaming modes:
  - Streaming: Shows real-time text as it arrives, then final markdown panel
  - Non-streaming: Shows spinner, then final markdown panel

  Args:
    user_input: The user's message/question to send to the agent
    token: Optional authentication token for secure agent communication

  Raises:
    Exception: Re-raises any unhandled exceptions after logging them

  Note:
    This function handles three types of streaming events:
    - Task: Initial task creation (usually empty content)
    - TaskArtifactUpdateEvent: Contains the actual response content
    - TaskStatusUpdateEvent: Status updates (usually empty content)
  """
  debug_log(f"Received user input: {user_input}")
  try:
    # Prepare headers for authentication if token is provided
    headers = {}
    if token:
      headers['Authorization'] = f'Bearer {token}'

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0), headers=headers) as httpx_client:
      debug_log(f"Connecting to agent at {AGENT_URL}")
      client = await A2AClient.get_client_from_agent_card_url(httpx_client, AGENT_URL)
      client.url = AGENT_URL  # Ensure the client uses the correct URL
      debug_log("Successfully connected to agent")

      payload = create_send_message_payload(user_input)
      debug_log(f"Created payload with message ID: {payload['message']['messageId']}")

      # Try streaming first (preferred mode for real-time user experience)
      try:
        # Create streaming request with unique ID and message payload
        streaming_request = SendStreamingMessageRequest(
          id=uuid4().hex,
          params=MessageSendParams(**payload),
        )
        debug_log(f"Sending streaming message to agent at {client.url}...")

        # Initialize streaming state variables
        chunk_count = 0
        final_state_text = ""
        all_text = ""
        partial_result_text = ""
        last_event_signature = ""
        final_response_text = ""  # Will be set after Live context exits

        execution_markdown = ""
        tool_entries: list[str] = []
        tool_seen: set[str] = set()
        tool_markdown = ""
        response_stream_buffer = ""
        response_markdown = ""  # Only used for Live dashboard (will stay empty for final response)
        streaming_markdown = ""
        spinner_stopped = False  # Track if we've stopped the spinner
        live_started = False  # Track if Live dashboard has been initialized
        live = None  # Will be initialized when execution plan arrives

        stream = client.send_message_streaming(streaming_request)

        def update_live() -> None:
          if live is not None:
            live.update(build_dashboard(execution_markdown, tool_markdown, response_markdown, streaming_markdown))

        async for chunk in stream:
            chunk_count += 1
            debug_log(f"Received streaming chunk #{chunk_count}: {type(chunk)}")
            debug_log(f"Chunk {chunk}")

            # Extract the actual event from the streaming response wrapper
            event = chunk.root.result
            event_type = type(event).__name__

            # Debug: Log event type and key attributes
            artifact_name = None
            if hasattr(event, 'artifact') and event.artifact and hasattr(event.artifact, 'name'):
                artifact_name = event.artifact.name

            # Extract metadata from the raw chunk if available (A2A SDK might not parse it into the event object)
            chunk_metadata = None
            if hasattr(chunk, 'root') and hasattr(chunk.root, 'result'):
              try:
                result_dict = chunk.root.result.model_dump(mode='json') if hasattr(chunk.root.result, 'model_dump') else None
                if isinstance(result_dict, dict):
                  chunk_metadata = result_dict.get('metadata')
                  if chunk_metadata:
                    debug_log(f"Found metadata in chunk result: {chunk_metadata}")
              except Exception as e:
                debug_log(f"Could not extract metadata from chunk: {e}")

            debug_log("=" * 80)
            debug_log(f"EVENT #{chunk_count}: Type={event_type}, Artifact={artifact_name}, Has_Status={hasattr(event, 'status')}")
            debug_log(f"Event attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
            # Check for metadata on the event
            if hasattr(event, 'metadata'):
              debug_log(f"Event has metadata attribute: {event.metadata}")
            elif hasattr(event, '__dict__'):
              debug_log(f"Event __dict__: {event.__dict__}")

            text = ""
            intermediate_state = False

            # Get artifact name early to decide if we should extract text
            artifact_name = None
            if hasattr(event, 'artifact') and event.artifact and hasattr(event.artifact, 'name'):
              artifact_name = event.artifact.name

            if getattr(event, 'status', None):
              text = _flatten_text_from_message_dict(event.status.message)
              debug_log(f"Extracted text from status: '{text}'")
              if event.status.state in [TaskState.working]:
                intermediate_state = True

              # Check if this is a tool notification via TaskStatusUpdateEvent
              # Tool notifications now use TaskStatusUpdateEvent with metadata.tool_notification=True
              # Try to get metadata from event object first, then from chunk if available
              event_metadata = getattr(event, 'metadata', None) or chunk_metadata or {}
              debug_log(f"TaskStatusUpdateEvent metadata: {event_metadata} (from event: {getattr(event, 'metadata', None)}, from chunk: {chunk_metadata})")
              if event_metadata and event_metadata.get('tool_notification'):
                # This is a tool notification - handle it in Tools Update Panel
                tool_status = event_metadata.get('status', 'started')
                tool_name = event_metadata.get('tool_name', 'unknown')
                debug_log(f"Tool notification detected: tool_name={tool_name}, status={tool_status}")

                # Stop spinner if not already stopped
                if not spinner_stopped:
                  notify_streaming_started()
                  try:
                    await wait_spinner_cleared()
                  except Exception:
                    pass
                  spinner_stopped = True

                # Format notification text
                if tool_status == 'started':
                  notification_text = summarize_tool_notification(text) or f"Calling {tool_name}"
                  if notification_text and notification_text not in tool_seen:
                    tool_seen.add(notification_text)
                    tool_entries.append(f"⏳ {notification_text}")
                    recent = tool_entries[-8:]
                    tool_markdown = "\n".join(f"- {line}" for line in recent)

                    # Append tool started notification to execution plan
                    # Extract the tool name from notification_text
                    tool_display_name = notification_text.replace("⏳", "").replace("Calling", "").strip()
                    # Clean up common patterns like "Calling Tool X" -> "X"
                    tool_display_name = tool_display_name.replace("Tool ", "").strip()
                    execution_item = f"- ⏳ Tool {tool_display_name} started"

                    if execution_markdown:
                      # Append to execution plan if not already present
                      if execution_item not in execution_markdown:
                        # Find the last checklist item and append after it
                        execution_lines = execution_markdown.split('\n')
                        last_item_idx = -1
                        for i in range(len(execution_lines) - 1, -1, -1):
                          line = execution_lines[i].strip()
                          if line and (line.startswith('- ✅') or line.startswith('- ❌') or line.startswith('- ⏳') or line.startswith('- 🔄')):
                            last_item_idx = i
                            break
                        if last_item_idx >= 0:
                          execution_lines.insert(last_item_idx + 1, execution_item)
                        else:
                          # No checklist items found, append at the end
                          execution_lines.append(execution_item)
                        execution_markdown = '\n'.join(execution_lines)
                    else:
                      # No execution plan yet, create a simple one
                      execution_markdown = f"📋 **Execution Plan**\n\n{execution_item}"

                    update_live()
                elif tool_status in ['completed', 'failed']:
                  completion_text = summarize_tool_notification(text) or f"{tool_name} {tool_status}"
                  if completion_text and completion_text not in tool_seen:
                    tool_seen.add(completion_text)
                    icon = "❌" if tool_status == 'failed' else "✅"
                    tool_entries.append(f"{icon} {completion_text}")
                    recent = tool_entries[-8:]
                    tool_markdown = "\n".join(f"- {line}" for line in recent)

                    # Update tool completion in execution plan
                    # Extract the tool name from completion_text (remove emoji and status words)
                    tool_display_name = completion_text.replace(icon, "").replace("completed", "").replace("failed", "").strip()
                    # Clean up common patterns like "Tool X completed" -> "X"
                    tool_display_name = tool_display_name.replace("Tool ", "").strip()
                    status_text = "completed" if tool_status == 'completed' else "failed"
                    execution_item = f"- {icon} Tool {tool_display_name} {status_text}"
                    started_item = f"- ⏳ Tool {tool_display_name} started"

                    if execution_markdown:
                      execution_lines = execution_markdown.split('\n')
                      # First, try to find and replace an existing ⏳ item for this tool
                      replaced = False
                      for i, line in enumerate(execution_lines):
                        if line.strip() == started_item:
                          execution_lines[i] = execution_item
                          replaced = True
                          break

                      # If not replaced, append as new item
                      if not replaced and execution_item not in execution_markdown:
                        # Find the last checklist item and append after it
                        last_item_idx = -1
                        for i in range(len(execution_lines) - 1, -1, -1):
                          line = execution_lines[i].strip()
                          if line and (line.startswith('- ✅') or line.startswith('- ❌') or line.startswith('- ⏳') or line.startswith('- 🔄')):
                            last_item_idx = i
                            break
                        if last_item_idx >= 0:
                          execution_lines.insert(last_item_idx + 1, execution_item)
                        else:
                          # No checklist items found, append at the end
                          execution_lines.append(execution_item)

                      execution_markdown = '\n'.join(execution_lines)
                    else:
                      # No execution plan yet, create a simple one
                      execution_markdown = f"📋 **Execution Plan**\n\n{execution_item}"

                    update_live()

                # Don't add tool notifications to streaming output
                continue

            elif hasattr(event, 'artifact') and event.artifact:
              # Skip text extraction for artifacts that shouldn't go into streaming buffer
              if artifact_name not in ['tool_notification_start', 'tool_notification_end',
                                        'execution_plan_update', 'execution_plan_status_update',
                                        'execution_plan_streaming']:
                artifact = event.artifact
                debug_log(f"🔍 Found artifact: name='{artifact_name}', type={type(artifact)}, has parts: {hasattr(artifact, 'parts')}")
                if hasattr(artifact, 'parts') and artifact.parts:
                  debug_log(f"🔍 Artifact has {len(artifact.parts)} parts")
                  for j, part in enumerate(artifact.parts):
                    debug_log(f"🔍 Part {j}: type={type(part)}, has text={hasattr(part, 'text')}, has root={hasattr(part, 'root')}")
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                      part_text = part.root.text
                      text += part_text
                      debug_log(f"🔍 Extracted from part[{j}].root.text: {len(part_text)} chars")
                    elif hasattr(part, 'text'):
                      part_text = part.text
                      text += part_text
                      debug_log(f"🔍 Extracted from part[{j}].text: {len(part_text)} chars")
                    elif hasattr(part, 'kind') and part.kind == 'text' and hasattr(part, 'text'):
                      part_text = part.text
                      text += part_text
                      debug_log(f"🔍 Extracted from part[{j}].kind=text: {len(part_text)} chars")
                    else:
                      debug_log(f"🔍 Part {j} has no extractable text - attributes: {[attr for attr in dir(part) if not attr.startswith('_')]}")
                else:
                  debug_log(f"🔍 Artifact '{artifact_name}' has no parts or parts is empty")
                debug_log(f"🔍 Total extracted text from artifact '{artifact_name}': {len(text)} chars, preview: '{text[:100]}...'")
              else:
                # Still extract for tool notifications but they'll be handled specially
                artifact = event.artifact
                if hasattr(artifact, 'parts') and artifact.parts:
                  for part in artifact.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                      text += part.root.text
                    elif hasattr(part, 'text'):
                      text += part.text
                debug_log(f"Extracted text from special artifact '{artifact_name}': {len(text)} chars")

            if artifact_name:

              if artifact_name == 'partial_result':
                debug_log(f"Step 2: Received partial_result event with {len(text)} chars")
                if text:
                  partial_result_text = sanitize_stream_text(text)
                  debug_log(f"Step 2: After sanitization: {len(partial_result_text)} chars")
                  debug_log(f"Step 2: First 200 chars: {partial_result_text[:200]}")
                  # Store partial result for use after Live context exits
                  # DON'T set response_markdown here - that displays it in Live dashboard
                  # We'll use partial_result_text after the Live context exits
                # DON'T clear streaming panel yet - keep it visible until we exit Live context
                # streaming_markdown will be cleared after the Live context exits
                update_live()
                continue

              if artifact_name in ['complete_result', 'final_result']:
                debug_log(f"Step 2: Received {artifact_name} event with {len(text)} chars")
                if text:
                  # Handle complete_result/final_result the same way as partial_result
                  # These are clean final results that should replace streaming content
                  complete_result_text = sanitize_stream_text(text)
                  debug_log(f"Step 2: After sanitization: {len(complete_result_text)} chars")
                  debug_log(f"Step 2: First 200 chars: {complete_result_text[:200]}")
                  # Store complete result for use after Live context exits
                  # Prefer complete_result over partial_result if both are present
                  if not partial_result_text or artifact_name == 'complete_result':
                    partial_result_text = complete_result_text
                    debug_log(f"Step 2: Using {artifact_name} for final display")
                # DON'T clear streaming panel yet - keep it visible until we exit Live context
                update_live()
                continue

              if artifact_name == 'execution_plan_update':
                if text:
                  execution_markdown = format_execution_plan_text(text)
                  # Stop spinner and start Live dashboard when execution plan arrives
                  if not spinner_stopped:
                    notify_streaming_started()
                    try:
                      await wait_spinner_cleared()
                    except Exception:
                      pass  # Spinner already cleared or not running
                    spinner_stopped = True
                  # Lazy initialize Live dashboard
                  if not live_started:
                    live = Live(build_dashboard(execution_markdown, tool_markdown, response_markdown, streaming_markdown),
                               console=console,
                               refresh_per_second=15,
                               transient=False)
                    live.start()
                    live_started = True
                  update_live()
                continue

              if artifact_name == 'execution_plan_status_update':
                if text:
                  execution_markdown = format_execution_plan_text(text)
                  # Stop spinner and start Live dashboard when execution plan arrives
                  if not spinner_stopped:
                    notify_streaming_started()
                    try:
                      await wait_spinner_cleared()
                    except Exception:
                      pass  # Spinner already cleared or not running
                    spinner_stopped = True
                  # Lazy initialize Live dashboard
                  if not live_started:
                    live = Live(build_dashboard(execution_markdown, tool_markdown, response_markdown, streaming_markdown),
                               console=console,
                               refresh_per_second=15,
                               transient=False)
                    live.start()
                    live_started = True
                  update_live()
                continue

              if artifact_name == 'execution_plan_streaming':
                continue

              if artifact_name == 'tool_notification_start' and text:
                # Stop spinner if not already stopped (fallback in case no execution plan)
                if not spinner_stopped:
                  notify_streaming_started()
                  try:
                    await wait_spinner_cleared()
                  except Exception:
                    pass
                  spinner_stopped = True
                notification_text = summarize_tool_notification(text)
                if notification_text and notification_text not in tool_seen:
                  tool_seen.add(notification_text)
                  tool_entries.append(f"⏳ {notification_text}")
                  recent = tool_entries[-8:]
                  tool_markdown = "\n".join(f"- {line}" for line in recent)
                  update_live()
                # Don't add tool notifications to streaming output
                continue

              if artifact_name == 'tool_notification_end' and text:
                completion_text = summarize_tool_notification(text)
                if completion_text and completion_text not in tool_seen:
                  tool_seen.add(completion_text)
                  tool_entries.append(f"✅ {completion_text}")
                  recent = tool_entries[-8:]
                  tool_markdown = "\n".join(f"- {line}" for line in recent)
                  update_live()
                # Don't add tool notifications to streaming output
                continue

              # Note: complete_result and final_result are now handled above (lines 1013-1028)
              # They're extracted and stored in partial_result_text for final display

            # Process text for streaming display
            # Only process text from artifacts, NOT from status messages
            # Status messages are metadata and should not go into the response buffer
            # streaming_result: Goes into streaming panel AND response_stream_buffer
            # partial_result: Already handled above with continue at line 930
            # tool_notification_*: Already handled above with continue at lines 991, 1010
            # TaskStatusUpdateEvent with tool_notification: Already handled above with continue at line 936
            # execution_plan_*: Already handled above with continue at lines 944, 966, 988
            # By this point, we only have streaming_result artifacts (status text is skipped)
            # Tool notifications are handled via TaskStatusUpdateEvent with metadata, so they should NOT appear in streaming_result
            if text and artifact_name:
              debug_log(f"🔍 Processing artifact '{artifact_name}' with {len(text)} chars of text")
              # Stop spinner if not already stopped (fallback for streaming content)
              if not spinner_stopped:
                debug_log("🔍 Stopping spinner and initializing Live dashboard")
                notify_streaming_started()
                try:
                  await wait_spinner_cleared()
                except Exception:
                  pass
                spinner_stopped = True

              # Initialize Live dashboard if not already started (for streaming_result that arrives before execution plan)
              if not live_started:
                debug_log("🔍 Initializing Live dashboard for streaming_result")
                live = Live(build_dashboard(execution_markdown, tool_markdown, response_markdown, streaming_markdown),
                           console=console,
                           refresh_per_second=15,
                           transient=False)
                live.start()
                live_started = True
                debug_log("🔍 Live dashboard initialized and started")
              else:
                debug_log("🔍 Live dashboard already started")

              clean_streaming_text = sanitize_stream_text(text)
              debug_log(f"🔍 After sanitization: {len(clean_streaming_text)} chars")
              if not clean_streaming_text:
                debug_log("🔍 Skipping empty text after sanitization")
                continue

              # Deduplicate: skip if this exact text was just processed
              signature = clean_streaming_text.strip()
              if signature == last_event_signature:
                continue
              last_event_signature = signature

              # Accumulate streaming text (token-by-token or chunk-by-chunk)
              # Check if this is a progressive update (new text contains old text)
              if response_stream_buffer.strip() and signature.startswith(response_stream_buffer.strip()):
                # New text is an extension of old text, replace with full version
                response_stream_buffer = clean_streaming_text
              elif response_stream_buffer.strip() and response_stream_buffer.strip() in signature:
                # New text contains old text somewhere, replace with full version
                response_stream_buffer = clean_streaming_text
              else:
                # New independent chunk - check if we need a space
                # Add space if both buffer and new chunk don't already have whitespace at boundaries
                if response_stream_buffer and not response_stream_buffer.endswith((' ', '\n', '\t')) and not clean_streaming_text.startswith((' ', '\n', '\t')):
                  response_stream_buffer += ' ' + clean_streaming_text
                else:
                  response_stream_buffer += clean_streaming_text

              if not intermediate_state:
                final_state_text = response_stream_buffer
              all_text = response_stream_buffer
              streaming_markdown = response_stream_buffer
              update_live()

            if hasattr(event, 'is_task_complete') and event.is_task_complete:
              # DON'T clear streaming panel - keep it visible until we exit Live context
              # The final response will be shown after Live context exits
              update_live()
              break

        debug_log(f"Streaming completed with {chunk_count} chunks")

        # STEP 1 COMPLETE: Streaming lines tracked
        debug_log(f"Step 1: Tracked streaming content - {len(response_stream_buffer)} chars")

        # STEP 2 COMPLETE: Prepare final response for display outside Live context
        # Prefer streaming buffer if it contains UserInputMetaData, otherwise use partial_result
        # This ensures we get the structured JSON format

        # Check if streaming buffer has UserInputMetaData
        has_user_input_metadata = False
        if response_stream_buffer and 'UserInputMetaData:' in response_stream_buffer:
          debug_log("Step 2: UserInputMetaData detected in streaming buffer")
          has_user_input_metadata = True

        if has_user_input_metadata:
          # Use streaming buffer to preserve UserInputMetaData
          debug_log(f"Step 2: Using streaming buffer for UserInputMetaData ({len(response_stream_buffer)} chars)")
          clean_text = sanitize_stream_text(response_stream_buffer)
          if clean_text:
            final_response_text = clean_text
            debug_log(f"Step 2: final_response_text set from streaming buffer: {len(final_response_text)} chars")
        elif partial_result_text:
          debug_log(f"Step 2: Using partial_result for final display ({len(partial_result_text)} chars)")
          debug_log(f"Step 2: partial_result_text first 200 chars: {partial_result_text[:200]}")
          final_response_text = partial_result_text
          debug_log(f"Step 2: final_response_text set to {len(final_response_text)} chars")
        elif response_stream_buffer or final_state_text or all_text:
          debug_log("Step 2: No partial_result, using accumulated streaming text")
          text_to_render = final_state_text if final_state_text else all_text
          if not text_to_render:
            text_to_render = response_stream_buffer

          if text_to_render:
            # Use sanitize_stream_text for comprehensive cleaning
            clean_text = sanitize_stream_text(text_to_render)
            debug_log(f"Step 2: After sanitization: {len(clean_text)} chars")
            debug_log(f"Step 2: First 200 chars: {clean_text[:200]}")

            if clean_text:
              # Store for rendering outside Live context
              final_response_text = clean_text

        # Clear streaming markdown and update one final time
        # DON'T set response_markdown - keep it empty so it won't render in Live dashboard
        streaming_markdown = ""
        update_live()

        # Stop Live dashboard if it was started
        if live_started and live is not None:
          live.stop()

        # Debug output (only when DEBUG mode is enabled)
        if DEBUG:
          if final_response_text:
            debug_log(f"final_response_text length = {len(final_response_text)} chars")
            debug_log(f"First 200 chars = {final_response_text[:200]}")
            debug_log(f"Contains 'ArgoCD' = {'ArgoCD' in final_response_text or 'argocd' in final_response_text.lower()}")
            debug_log(f"Contains 'Supervisor' = {'Supervisor' in final_response_text}")
          else:
            debug_log("final_response_text is EMPTY!")
            debug_log(f"partial_result_text length = {len(partial_result_text) if partial_result_text else 0}")
            debug_log(f"response_stream_buffer length = {len(response_stream_buffer)}")

        # Final render outside Live context - use final_response_text
        if final_response_text:
          # Parse for structured metadata (dynamic forms)
          parsed = parse_structured_response(final_response_text)
          content_text = parsed["content"]

          # Check if we have user input metadata
          if parsed.get("require_user_input") and parsed.get("metadata"):
            debug_log("🎨 User input required - rendering form")
            # Render the explanation text first
            render_answer(content_text, agent_name=agent_name.capitalize() if agent_name else "AI Platform Engineer")

            # Then render the interactive form
            user_data = render_metadata_form(parsed["metadata"], console)

            if user_data:
              # User provided input, send follow-up message
              debug_log(f"📝 User provided input: {user_data}")
              # Format the user input as a readable message
              formatted_input = "\n".join([f"- {k}: {v}" for k, v in user_data.items()])
              await handle_user_input(f"Here's the information you requested:\n{formatted_input}", token)
              return
            else:
              debug_log("❌ User cancelled input")
              return

          # No metadata, just render the response
          render_answer(content_text, agent_name=agent_name.capitalize() if agent_name else "AI Platform Engineer")

        return

      except Exception as stream_err:
        if DEBUG:
          debug_log(f"EXCEPTION in streaming: {type(stream_err).__name__}: {stream_err}")
          import traceback
          traceback.print_exc()
        debug_log(f"Streaming not available or failed: {stream_err}. Falling back to non-streaming.")

      # Fallback: non-streaming request
      request = SendMessageRequest(
        id=uuid4().hex,
        params=MessageSendParams(**payload)
      )
      debug_log(f"Sending non-streaming message to agent at {client.url}...")
      response: SendMessageResponse = await client.send_message(request)
      debug_log("Received response from agent (non-streaming)")

      if isinstance(response.root, SendMessageSuccessResponse):
        debug_log("Agent returned success response")
        text = extract_response_text(response)

        # Show original question for context (non-streaming fallback)
        print(f"💬 You: {user_input}")

        # Parse for structured metadata (dynamic forms)
        parsed = parse_structured_response(text)
        content_text = parsed["content"]

        # Render the main response
        render_answer(content_text, agent_name=agent_name.capitalize() if agent_name else "AI Platform Engineer")

        # Check if user input is required (non-streaming fallback)
        if parsed["require_user_input"] and parsed["metadata"]:
          debug_log("🎨 Structured metadata detected (non-streaming) - rendering form")

          # Render interactive form
          form_data = render_metadata_form(parsed["metadata"])

          if form_data:
            # User submitted form - send data back as structured JSON
            debug_log(f"📤 Sending form data back to agent: {form_data}")

            # Format as JSON for the agent
            metadata_response = json.dumps(form_data, indent=2)

            # Recursively call handle_user_input with the metadata response
            await handle_user_input(metadata_response, token)
          else:
            print("[yellow]No input provided. You can ask another question.[/yellow]")
      else:
        print(f"❌ Agent returned a non-success response: {response.root}")

  except Exception as e:
    print(f"ERROR: Exception occurred: {str(e)}")
    raise

async def fetch_agent_card(host, port, token: str, tls: bool) -> AgentCard:
  """
  Fetch the agent card, preferring the authenticated extended card if supported.
  """
  if tls:
    base_url = f"https://{host}:{port}"
  else:
    base_url = f"http://{host}:{port}"

  PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
  EXTENDED_AGENT_CARD_PATH = '/agent/authenticatedExtendedCard'

  async with httpx.AsyncClient() as httpx_client:
    resolver = A2ACardResolver(
      httpx_client=httpx_client,
      base_url=base_url,
    )
    final_agent_card_to_use: AgentCard | None = None

    try:
      logger.debug(f'Attempting to fetch public agent card from: {base_url}{PUBLIC_AGENT_CARD_PATH}')
      _public_card = await resolver.get_agent_card()
      logger.debug('Successfully fetched public agent card:')
      logger.debug(_public_card.model_dump_json(indent=2, exclude_none=True))
      final_agent_card_to_use = _public_card
      logger.debug('\nUsing PUBLIC agent card for client initialization (default).')

      if getattr(_public_card, "supportsAuthenticatedExtendedCard", False):
        try:
          logger.debug(f'\nPublic card supports authenticated extended card. Attempting to fetch from: {base_url}{EXTENDED_AGENT_CARD_PATH}')
          auth_headers_dict = {'Authorization': f'Bearer {token}'}
          _extended_card = await resolver.get_agent_card(
            relative_card_path=EXTENDED_AGENT_CARD_PATH,
            http_kwargs={'headers': auth_headers_dict},
          )
          logger.debug('Successfully fetched authenticated extended agent card:')
          logger.debug(_extended_card.model_dump_json(indent=2, exclude_none=True))
          final_agent_card_to_use = _extended_card
          logger.debug('\nUsing AUTHENTICATED EXTENDED agent card for client initialization.')
        except Exception as e_extended:
          logger.warning(f'Failed to fetch extended agent card: {e_extended}. Will proceed with public card.', exc_info=True)
      elif _public_card:
        logger.debug('\nPublic card does not indicate support for an extended card. Using public card.')

    except Exception as e:
      logger.error(f'Critical error fetching public agent card: {e}', exc_info=True)
      raise RuntimeError('Failed to fetch the public agent card. Cannot continue.') from e

    return final_agent_card_to_use


def main(host, port, token, tls):
  # Get CLI version
  cli_version = "unknown"
  try:
    from agent_chat_cli.__main__ import __version__
    cli_version = __version__
  except ImportError:
    pass

  # Fetch the agent card before running the chat loop
  agent_card = asyncio.run(fetch_agent_card(host, port, token, tls))
  global agent_name
  agent_name = agent_card.name if hasattr(agent_card, "name") else "Agent"

  # Display welcome panel with version
  from rich.console import Console
  from rich.panel import Panel
  from rich.align import Align

  welcome_console = Console()
  welcome_text = f"🚀 **agent-chat-cli** v{cli_version}\n\n✅ Connected to **{agent_name}**"
  welcome_panel = Panel(
    Align.center(welcome_text, vertical="middle"),
    title="Welcome to AI Platform Engineer CLI",
    title_align="center",
    border_style="bold cyan",
    padding=(1, 2)
  )
  welcome_console.print(welcome_panel)
  print()  # Add spacing
  skills_description = ""
  skills_examples = []

  if hasattr(agent_card, "skills") and agent_card.skills:
    skill = agent_card.skills[0]
    skills_description = skill.description if hasattr(skill, "description") else ""
    skills_examples = skill.examples if hasattr(skill, "examples") else []

  logger.debug(f"Agent name: {agent_name}")
  logger.debug(f"Skills description: {skills_description}")
  logger.debug(f"Skills examples: {skills_examples}")

  # Clear the console and print a header
  console.clear()
  asyncio.run(run_chat_loop(
    lambda user_input: handle_user_input(user_input, token),
    agent_name=agent_name,
    skills_description=skills_description,
    skills_examples=skills_examples
  ))
