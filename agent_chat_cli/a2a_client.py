# Copyright CNOE Contributors (https://cnoe.io)
# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
import logging
import sys
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
  SendStreamingMessageRequest,  # ADD
  # The following may exist depending on SDK version; safe to add if present:
  # TaskStatusUpdateEvent,      # OPTIONAL (only if you want isinstance checks)
  # TaskState,                  # OPTIONAL (for state comparisons)
)
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
console = Console()

SESSION_CONTEXT_ID = uuid4().hex

def debug_log(message: str):
  if DEBUG:
    print(f"DEBUG: {message}")

def create_send_message_payload(text: str) -> dict[str, Any]:
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
  try:
    if hasattr(response, "model_dump"):
      response_data = response.model_dump()
    elif hasattr(response, "dict"):
      response_data = response.dict()
    elif isinstance(response, dict):
      response_data = response
    else:
      raise ValueError("Unsupported response type")

    result = response_data.get("result", {})

    artifacts = result.get("artifacts")
    if artifacts and isinstance(artifacts, list) and artifacts[0].get("parts"):
      for part in artifacts[0]["parts"]:
        if part.get("kind") == "text":
          return part.get("text", "").strip()

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
  Given a message object/dict, return the concatenated text content.
  Supports both {text: "..."} and {parts: [{kind|type: 'text', text: '...'}]} shapes.
  """
  try:
    if hasattr(message, "model_dump"):
      message = message.model_dump()
    elif hasattr(message, "dict"):
      message = message.dict()

    if not isinstance(message, dict):
      return ""

    # Direct text on message
    if isinstance(message.get("text"), str):
      return message["text"]

    # Parts-based text
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



async def handle_user_input(user_input: str, token: str = None):
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

      # Try streaming first
      try:
        streaming_request = SendStreamingMessageRequest(
          id=uuid4().hex,
          params=MessageSendParams(**payload),
        )
        debug_log(f"Sending streaming message to agent at {client.url}...")
        first_content_received = False
        chunk_count = 0
        collected_text = ""
        async for chunk in client.send_message_streaming(streaming_request):
          chunk_count += 1
          debug_log(f"Received streaming chunk #{chunk_count}: {type(chunk)}")

          event = chunk.root.result
          debug_log(f"Processing event: {type(event)}, has status: {hasattr(event, 'status')}")
          debug_log(f"Event attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")

          # Handle different event types
          text = ""
          if getattr(event, 'status', None):
            # Task or TaskStatusUpdateEvent with status
            text = _flatten_text_from_message_dict(event.status.message)
            debug_log(f"Extracted text from status: '{text}'")
          elif hasattr(event, 'artifact') and event.artifact:
            # TaskArtifactUpdateEvent with artifact (singular)
            artifact = event.artifact
            debug_log(f"Found artifact: {type(artifact)}, has parts: {hasattr(artifact, 'parts')}")
            if hasattr(artifact, 'parts') and artifact.parts:
              debug_log(f"Artifact has {len(artifact.parts)} parts")
              for j, part in enumerate(artifact.parts):
                debug_log(f"Part {j}: {type(part)}, attributes: {[attr for attr in dir(part) if not attr.startswith('_')]}")
                if hasattr(part, 'text'):
                  text += part.text
                  debug_log(f"Added text from part.text: '{part.text}'")
                elif hasattr(part, 'kind') and part.kind == 'text' and hasattr(part, 'text'):
                  text += part.text
                  debug_log(f"Added text from part.kind=text: '{part.text}'")
                elif hasattr(part, 'root') and hasattr(part.root, 'text'):
                  text += part.root.text
                  debug_log(f"Added text from part.root.text: '{part.root.text}'")
            else:
              debug_log(f"Artifact: {artifact}")
            debug_log(f"Extracted text from artifact: '{text}'")

          # Only stop spinner when we have actual content to display
          if text and not first_content_received:
            notify_streaming_started()          # stop spinner; it will replace spinner with an arrow on same line
            try:
              await wait_spinner_cleared()      # wait until spinner finalized
            except Exception:
              await asyncio.sleep(0)            # best-effort fallback
            sys.stdout.write("\n")              # start the streaming response on a new line
            sys.stdout.flush()
            first_content_received = True
          
          # Show streaming text immediately AND collect it for final rendering
          if text:
            print(text, end="", flush=True)    # Show streaming text in real-time
            collected_text += text
        
        debug_log(f"Streaming completed with {chunk_count} chunks")
        
        # Show final result in a beautiful markdown panel
        if collected_text:
          print("\n")  # Add some space before the final panel
          render_answer(collected_text, agent_name="AI Platform Engineer")
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
        render_answer(text)
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
