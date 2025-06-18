# Copyright CNOE Contributors (https://cnoe.io)
# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
import json
import logging
from uuid import uuid4
from typing import Any

from rich.console import Console
from agent_chat_cli.chat_interface import run_chat_loop, render_answer

import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
  SendMessageResponse,
  SendMessageSuccessResponse,
  SendMessageRequest,
  MessageSendParams,
  AgentCard,
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

async def handle_user_input(user_input: str):
  debug_log(f"Received user input: {user_input}")
  try:
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as httpx_client:
      debug_log(f"Connecting to agent at {AGENT_URL}")
      client = await A2AClient.get_client_from_agent_card_url(httpx_client, AGENT_URL)
      debug_log("Successfully connected to agent")

      payload = create_send_message_payload(user_input)
      debug_log(f"Created payload with message ID: {payload['message']['messageId']}")

      request = SendMessageRequest(
        id=uuid4().hex,
        params=MessageSendParams(**payload)
      )
      debug_log("Sending message to agent...")

      response: SendMessageResponse = await client.send_message(request)
      debug_log("Received response from agent")

      if isinstance(response.root, SendMessageSuccessResponse):
        debug_log("Agent returned success response")
        debug_log("Response JSON:")
        debug_log(json.dumps(response.root.dict(), indent=2, default=str))
        text = extract_response_text(response)
        debug_log(f"Extracted text (first 100 chars): {text[:100]}...")
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
    handle_user_input,
    agent_name=agent_name,
    skills_description=skills_description,
    skills_examples=skills_examples
  ))