# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
import re
from uuid import uuid4
from typing import Any
from rich.markdown import Markdown
from rich.console import Console
from agent_chat_cli.chat_interface import run_chat_loop, render_answer

import httpx
from a2a.client import A2AClient
import json
from a2a.types import (
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendMessageRequest,
    MessageSendParams,
)
import warnings
import logging

warnings.filterwarnings(
    "ignore",
    message=".*`dict` method is deprecated.*",
    category=DeprecationWarning,
    module=".*"
)

# Configure root logger
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# Suppress logging for 'a2a' module to WARNING
logging.getLogger("a2a").setLevel(logging.WARNING)

AGENT_HOST = os.environ.get("A2A_AGENT_HOST", "localhost")
AGENT_PORT = os.environ.get("A2A_AGENT_PORT", "8000")
AGENT_URL = f"http://{AGENT_HOST}:{AGENT_PORT}"
DEBUG = os.environ.get("A2A_DEBUG_CLIENT", "false").lower() in ["1", "true", "yes"]
console = Console()

# Generate a context ID when the script starts - this will be used for the entire session
SESSION_CONTEXT_ID = uuid4().hex

def debug_log(message: str):
    if DEBUG:
        print(f"DEBUG: {message}")

def create_send_message_payload(text: str) -> dict[str, Any]:
    message_id = uuid4().hex
    return {
        "id": message_id,
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": text}],
            "messageId": message_id,
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
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
            debug_log(f"Connecting to agent at {AGENT_URL}")
            client = await A2AClient.get_client_from_agent_card_url(httpx_client, AGENT_URL)
            debug_log("Successfully connected to agent")

            payload = create_send_message_payload(user_input)
            debug_log(f"Created payload with message ID: {payload['message']['messageId']}")

            request = SendMessageRequest(params=MessageSendParams(**payload))
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

def main(host: str = "localhost", port: int = 8000, token: str = None):
  """Main function to run the chat loop."""
  agent_name = os.getenv("AGENT_NAME", "")
  asyncio.run(run_chat_loop(handle_user_input, title=f"A2A {agent_name} Agent"))

if __name__ == "__main__":
  main()
