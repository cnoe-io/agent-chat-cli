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
import re
import shutil
from uuid import uuid4
from typing import Any

from rich.console import Console
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
    except:
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
    
    # Small delay to ensure terminal operations complete
    import time
    time.sleep(0.01)

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
  It supports both artifacts and status message formats.

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
    if artifacts and isinstance(artifacts, list) and artifacts[0].get("parts"):
      for part in artifacts[0]["parts"]:
        if part.get("kind") == "text":
          return part.get("text", "").strip()

    # Fallback to status message
    message = result.get("status", {}).get("message", {})
    for part in message.get("parts", []):
      if part.get("kind") == "text":
        return part.get("text", "").strip()
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
        first_content_received = False  # Track when to stop spinner
        chunk_count = 0                 # Debug counter for received chunks
        final_state_text = ""           # Text for final markdown panel - Only when task is complete
        all_text = ""                   # Text for final markdown panel - Accumulate all text (in case there are no final state)
        
        # Task notification tracking
        current_notification_line = ""  # Current notification being displayed
        
        # Simple deduplication tracking
        last_event_signature = ""       # Track last processed content to detect consecutive duplicates
        
        # Task notification tracking for precise removal from final output
        displayed_task_notifications = []  # Track exact notifications shown to user for filtering
        
        # Streaming content tracking for in-place replacement
        streaming_content = ""          # Accumulate all streamed content for line counting
        lines_printed = 0               # Track total lines printed (notifications + streaming content)
        user_question = user_input      # Preserve the original question for display


        # Process streaming response chunks as they arrive
        async for chunk in client.send_message_streaming(streaming_request):
          chunk_count += 1
          debug_log(f"Received streaming chunk #{chunk_count}: {type(chunk)}")
          debug_log(f"Chunk {chunk}")

          # Extract the actual event from the streaming response wrapper
          event = chunk.root.result
          debug_log(f"Processing event: {type(event)}, has status: {hasattr(event, 'status')}")
          debug_log(f"Event attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
          
          # Optional: Enhanced event debugging (uncomment for detailed debugging)
          # event_type = type(event).__name__
          # debug_log(f"Event type: {event_type}")
          # if hasattr(event, 'artifact') and event.artifact:
          #   debug_log(f"Artifact name: {getattr(event.artifact, 'name', 'unnamed')}")

          # Extract text content using duck typing approach (more flexible than isinstance)
          text = ""

          intermediate_state = False

          # Handle events with status (Task, TaskStatusUpdateEvent)
          if getattr(event, 'status', None):
            # These events typically contain status updates or initial task creation
            text = _flatten_text_from_message_dict(event.status.message)
            debug_log(f"Extracted text from status: '{text}'")

            if getattr(event, 'status', None) and event.status.state in [TaskState.working]:
              debug_log(f"Task is in progress: {event.status.state}")
              intermediate_state = True

          # Handle events with artifacts (TaskArtifactUpdateEvent) - contains actual response content
          elif hasattr(event, 'artifact') and event.artifact:
            artifact = event.artifact
            debug_log(f"Found artifact: {type(artifact)}, has parts: {hasattr(artifact, 'parts')}")

            # Process artifact parts to extract text content
            if hasattr(artifact, 'parts') and artifact.parts:
              debug_log(f"Artifact has {len(artifact.parts)} parts")
              for j, part in enumerate(artifact.parts):
                debug_log(f"Part {j}: {type(part)}, attributes: {[attr for attr in dir(part) if not attr.startswith('_')]}")

                # Try different text extraction patterns based on part structure
                if hasattr(part, 'text'):
                  # Direct text attribute
                  text += part.text
                  debug_log(f"Added text from part.text: '{part.text}'")
                elif hasattr(part, 'kind') and part.kind == 'text' and hasattr(part, 'text'):
                  # Text part with kind discriminator
                  text += part.text
                  debug_log(f"Added text from part.kind=text: '{part.text}'")
                elif hasattr(part, 'root') and hasattr(part.root, 'text'):
                  # Nested text in root structure
                  text += part.root.text
                  debug_log(f"Added text from part.root.text: '{part.root.text}'")
            else:
              debug_log(f"Artifact: {artifact}")
            debug_log(f"Extracted text from artifact: '{text}'")

          # Smart deduplication based on artifact type and streaming strategy
          event_type = type(event).__name__
          
          # Skip partial_result if we've been streaming content
          if hasattr(event, 'artifact') and event.artifact and hasattr(event.artifact, 'name'):
            artifact_name = event.artifact.name
            
            if artifact_name == 'partial_result':
              # Skip partial_result entirely if we've received streaming content
              if streaming_content.strip():
                debug_log(f"Skipping partial_result - already have streaming content ({len(streaming_content)} chars)")
                continue
              else:
                debug_log(f"Processing partial_result - no prior streaming content")
            
            elif artifact_name == 'streaming_result':
              # Track that we're receiving streaming content
              debug_log(f"Processing streaming_result chunk: {text[:50] if text else 'empty'}...")
          
          # Basic consecutive duplicate prevention (only for identical consecutive events)
          if text and text.strip():
            text_content = text.strip()
            
            # Skip only if exact same content from exact same event type consecutively
            if text_content == last_event_signature:
              debug_log(f"Skipping consecutive duplicate from {event_type}: {text_content[:50]}...")
              continue
            
            last_event_signature = text_content
          
          # Task notification detection and handling via artifact types
          task_notification_handled = False
          
          # Check for task notification artifacts
          if hasattr(event, 'artifact') and event.artifact and hasattr(event.artifact, 'name'):
            artifact_name = event.artifact.name
            debug_log(f"Processing artifact: {artifact_name} (event type: {event_type})")
            
            # Handle tool notification start
            if artifact_name == 'tool_notification_start':
              if text:
                notification_text = text.strip()
                
                # Check if we've already displayed this notification (simple string check)
                if notification_text.strip() not in displayed_task_notifications:
                  current_notification_line = notification_text
                  
                  # Stop spinner and move to new line for task notification
                  if not first_content_received:
                    notify_streaming_started()
                    try:
                      await wait_spinner_cleared()
                    except Exception:
                      await asyncio.sleep(0)
                    first_content_received = True
                    sys.stdout.write("\n")  # Move to new line after spinner
                    sys.stdout.flush()
                    lines_printed += 1  # Count newline after spinner
                  
                  # Display the task notification on new line
                  print(notification_text)
                  lines_printed += 1  # Count notification line
                  # Store the clean notification text for precise removal
                  displayed_task_notifications.append(notification_text.strip())
                  task_notification_handled = True
                  debug_log(f"Displayed task start notification: {notification_text}")
                else:
                  debug_log(f"Skipping duplicate task start notification: {notification_text}")
                  task_notification_handled = True
            
            # Handle tool notification end
            elif artifact_name == 'tool_notification_end':
              if text:
                completion_text = text.strip()
                
                # Check if we've already displayed this completion notification (simple string check)
                if completion_text.strip() not in displayed_task_notifications:
                  # Ensure spinner is stopped
                  if not first_content_received:
                    notify_streaming_started()
                    try:
                      await wait_spinner_cleared()
                    except Exception:
                      await asyncio.sleep(0)
                    first_content_received = True
                    sys.stdout.write("\n")  # Move to new line after spinner
                    sys.stdout.flush()
                    lines_printed += 1  # Count newline after spinner
                  
                  # Display completion notification on new line
                  print(completion_text)
                  lines_printed += 1  # Count notification line
                  # Store the clean notification text for precise removal
                  displayed_task_notifications.append(completion_text.strip())
                  task_notification_handled = True
                  current_notification_line = completion_text
                  debug_log(f"Displayed task completion notification: {completion_text}")
                else:
                  debug_log(f"Skipping duplicate task completion notification: {completion_text}")
                  task_notification_handled = True
          
          
          # Visual feedback management: stop spinner only when we have actual content (and not already handled)
          if text and not first_content_received and not task_notification_handled:
            # Transition from spinner to streaming display
            notify_streaming_started()          # Stop spinner; replaces with arrow (→) on same line
            try:
              await wait_spinner_cleared()      # Wait for spinner animation to complete
            except Exception:
              await asyncio.sleep(0)            # Best-effort fallback if spinner cleanup fails
            sys.stdout.write("\n")              # Start streaming response on a new line
            sys.stdout.flush()
            lines_printed += 1                   # Count the newline after spinner
            first_content_received = True

          # Dual display strategy: real-time streaming + final markdown panel
          if text and not task_notification_handled:
            print(text, end="", flush=True)    # Show streaming text immediately (no newlines)
            streaming_content += text          # Track for line counting
            if not intermediate_state:         # Avoid accumulating text for intermediate states
              final_state_text += text               # Accumulate for final formatted display
            all_text += text                   # Always accumulate all text (in case there are no final states)
          elif text:
            # For task notifications, still accumulate for final display but don't print immediately
            if not intermediate_state:
              final_state_text += text
            all_text += text

        debug_log(f"Streaming completed with {chunk_count} chunks")
        
        # Calculate total lines used for in-place replacement  
        total_lines = lines_printed  # Includes notification lines and newline after spinner
        if streaming_content:
          content_lines = count_display_lines(streaming_content)
          total_lines += content_lines
        
        debug_log(f"Total lines to clear: {total_lines} (notifications: {lines_printed}, content: {count_display_lines(streaming_content) if streaming_content else 0})")
        
        # Final presentation: render complete response in beautiful markdown panel
        text_to_render = final_state_text if final_state_text else all_text
        
        # Remove task notifications from final display to avoid duplication
        if text_to_render:
          clean_text = text_to_render
          
          # Remove exact task notifications that were displayed during streaming
          # Notifications are now stored as clean text (without extra newlines)
          for notification in displayed_task_notifications:
            if notification in clean_text:
              clean_text = clean_text.replace(notification, "")
              debug_log(f"Removed task notification from final text: {notification[:30]}...")
          
          # Clean up excessive newlines while preserving markdown structure
          clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)  # Max 2 consecutive newlines for markdown
          clean_text = clean_text.strip()
          
          if clean_text:
            # Clear all streamed content and replace with markdown panel (preserve original question)
            if total_lines > 0:
              # More conservative clearing - only clear if it seems reasonable
              if total_lines <= 50:  # Safety limit
                clear_lines(total_lines)
                debug_log(f"Cleared {total_lines} lines for in-place replacement")
                
                # Re-display the original question to maintain context
                print(f"💬 You: {user_question}")
              else:
                debug_log(f"Skipping clear - too many lines ({total_lines})")
                # Still show question for consistency, just add more spacing
                print(f"\n💬 You: {user_question}")
            else:
              # No clearing needed, but still show question for context
              print(f"\n💬 You: {user_question}")
            
            render_answer(clean_text, agent_name=agent_name.capitalize() if agent_name else "AI Platform Engineer")
            # render_answer handles its own spacing - no additional newlines needed
            debug_log(f"Filtered {len(displayed_task_notifications)} task notifications from final output")
        return

      except Exception as stream_err:
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
        
        render_answer(text, agent_name=agent_name.capitalize() if agent_name else "AI Platform Engineer")
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
  # Fetch the agent card before running the chat loop
  agent_card = asyncio.run(fetch_agent_card(host, port, token, tls))
  global agent_name
  agent_name = agent_card.name if hasattr(agent_card, "name") else "Agent"
  print(f"✅ A2A Agent Card detected for \033[1m\033[32m{agent_name}\033[0m")
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
