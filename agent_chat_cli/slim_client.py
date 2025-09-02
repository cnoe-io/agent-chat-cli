from typing import Any, Union, Optional
import asyncio
import json
import logging
import os
import re
from uuid import uuid4

import httpx
from rich.console import Console
from agent_chat_cli.chat_interface import run_chat_loop, render_answer
from a2a.types import (
    AgentCard,
    SendMessageRequest,
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
)
from agntcy_app_sdk.factory import AgntcyFactory, ProtocolTypes
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
console = Console()
# Set a2a.client logging to WARNING
logging.getLogger("a2a.client").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Default A2A topic for SLIM clients
TOPIC = "default/default/agent-slim"

_factory: AgntcyFactory = AgntcyFactory()
_transport: Any = None
_client: Any = None
_agent_name: str = "Agent"
_skills_description: str = ""
_skills_examples: list[str] = []
_endpoint: Optional[str] = None
_remote_card_raw: Optional[Union[str, AgentCard, dict]] = None
_remote_card_card: Optional[AgentCard] = None
_a2a_topic: Optional[str] = None


def _slugify_segment(s: Optional[str]) -> str:
    if not isinstance(s, str):
        return "default"
    v = s.strip().lower()
    v = re.sub(r"[^a-z0-9]+", "-", v)
    v = re.sub(r"-{2,}", "-", v).strip("-")
    return v or "default"

def _derive_valid_topic(card: Optional[AgentCard]) -> Optional[str]:
    base_topic = None
    if not card:
        logger.error("_derive_valid_topic: no AgentCard provided")
        return None
    try:
        base_topic = A2AProtocol.create_agent_topic(card)
        logger.debug(f"_derive_valid_topic: base_topic from SDK={base_topic!r}")
    except Exception as e:
        logger.debug(f"_derive_valid_topic: failed to get topic via SDK: {e}")

    local_candidate: Optional[str] = None
    if getattr(card, "name", None):
        local_candidate = card.name
    elif isinstance(base_topic, str) and base_topic:
        local_candidate = base_topic.rsplit("/", 1)[-1]

    if not local_candidate:
        logger.error("_derive_valid_topic: no name available on AgentCard and no SDK topic")
        return None

    local = _slugify_segment(local_candidate)
    topic = f"default/default/{local}"
    logger.debug(f"_derive_valid_topic: computed topic={topic!r}")
    return topic


async def _load_remote_card(remote_card: str) -> Union[AgentCard, str, dict]:
    """Load or parse a remote agent card from URL, JSON string, or file path."""
    s = remote_card.strip()
    logger.debug(f"_load_remote_card: input={remote_card!r}")
    try:
        if s.startswith(("http://", "https://")):
            async with httpx.AsyncClient() as client:
                resp = await client.get(s)
                resp.raise_for_status()
                data = resp.json()
                logger.debug(f"_load_remote_card: fetched JSON from URL ({s}), keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
        elif s.startswith("{"):
            data = json.loads(s)
            logger.debug(f"_load_remote_card: parsed JSON string, type={type(data)} keys={list(data.keys()) if isinstance(data, dict) else None}")
        elif os.path.exists(s):
            with open(s, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"_load_remote_card: loaded JSON from file {s}, keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
        else:
            logger.debug(f"_load_remote_card: treating as identifier/string subject: {s!r}")
            return s

        try:
            card = AgentCard(**data)
            logger.debug(f"_load_remote_card: constructed AgentCard: name={getattr(card,'name',None)!r}")
            return card
        except Exception as e:
            logger.debug(f"_load_remote_card: could not construct AgentCard from dict: {e}; returning dict")
            return data
    except Exception as e:
        logger.warning(f"_load_remote_card: failed to load: {e}; returning raw string")
        return s


def _extract_response_text(response) -> str:
    """Extract readable text from A2A SendMessageResponse-like objects."""
    try:
        if hasattr(response, "model_dump"):
            response_data = response.model_dump()
        elif hasattr(response, "dict"):
            response_data = response.dict()
        elif isinstance(response, dict):
            response_data = response
        else:
            return ""

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
            if "text" in part:
                return part["text"].strip()
    except Exception:
        pass
    return ""




async def _ensure_client():
    """Ensure A2A client exists; transport is created in main()."""
    global _client
    logger.debug(f"_ensure_client: _client is {'present' if _client else 'None'}")
    if _client is not None:
        return

    topic = _a2a_topic or TOPIC
    if not isinstance(topic, str) or topic.count("/") != 2:
        logger.error("_ensure_client: invalid agent_topic %r; cannot continue", topic)
        raise RuntimeError("Invalid agent topic derived from Agent Card. Please verify the agent is available and try again.")
    _client = await _factory.create_client(
        ProtocolTypes.A2A.value, agent_topic=topic, transport=_transport
    )
    logger.debug(f"_ensure_client: client created: {type(_client)}")



async def handle_user_input(user_input: str):
    """Send user input via SLIM and render the agent's response."""
    try:
        await _ensure_client()
        logger.debug(f"handle_user_input: building message for user_input len={len(user_input)}")
        parts = [Part(TextPart(text=user_input))]
        msg_kwargs: dict[str, Any] = {
            "messageId": str(uuid4()),
            "role": Role.user,
            "parts": parts,
        }


        logger.debug(f"handle_user_input: msg_kwargs keys={list(msg_kwargs.keys())}, metadata={msg_kwargs.get('metadata')}")

        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message=Message(**msg_kwargs)),
        )

        logger.debug(f"handle_user_input: sending message id={request.id} messageId={msg_kwargs['messageId']}")
        response = await _client.send_message(request)
        logger.debug(f"handle_user_input: received response type={type(response)}")
        try:
            logger.debug(f"handle_user_input: response preview={str(response)[:500]}")
        except Exception:
            pass
        text = _extract_response_text(response)
        logger.debug(f"handle_user_input: extracted text len={len(text)} preview={text[:200]!r}")
        render_answer(text, agent_name=_agent_name or "Agent")
    except Exception as e:
        logger.exception("handle_user_input: exception while sending/rendering")
        render_answer(f"❌ Error sending message: {e}", agent_name=_agent_name or "Agent")


def main(endpoint: str, remote_card: str, debug: bool = False):
    """CLI entry point for the SLIM client."""
    global _endpoint, _remote_card_raw, _agent_name, _skills_description, _skills_examples
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("agent_chat_cli").setLevel(logging.DEBUG)
        logging.getLogger("agent_chat_cli.slim_client").setLevel(logging.DEBUG)
        logging.getLogger("agntcy_app_sdk").setLevel(logging.DEBUG)

    _endpoint = endpoint
    if _endpoint and not _endpoint.startswith(("http://", "https://")):
        _endpoint = f"http://{_endpoint}"
        logger.debug(f"main: normalized SLIM endpoint to {_endpoint!r}")
    loaded_card = asyncio.run(_load_remote_card(remote_card))
    logger.debug(f"main: loaded_card type={type(loaded_card)}, value preview={str(loaded_card)[:200]}")
    _remote_card_raw = loaded_card

    # Normalize to AgentCard if possible
    card_obj: Optional[AgentCard] = None
    if isinstance(loaded_card, AgentCard):
        card_obj = loaded_card
    elif isinstance(loaded_card, dict):
        try:
            card_obj = AgentCard(**loaded_card)
        except Exception:
            card_obj = None
    logger.debug(f"main: normalized card_obj type={type(card_obj)} name={getattr(card_obj,'name',None)!r}")
    # Save normalized card for later topic creation
    globals()["_remote_card_card"] = card_obj

    if card_obj is None:
        console.print("[error]❌ Unable to load or parse remote Agent Card.[/error]")
        console.print("[warning]Please verify the agent is running and reachable, and that the remote card is available.[/warning]")
        console.print(f"[info]Remote card: {remote_card}[/info]")
        if _endpoint:
            console.print(f"[info]Endpoint: {_endpoint}[/info]")
        raise SystemExit(2)

    # Derive and normalize A2A topic from AgentCard
    a2a_topic_local = _derive_valid_topic(card_obj)
    if not (isinstance(a2a_topic_local, str) and a2a_topic_local.count("/") == 2):
        console.print("[error]❌ Unable to derive A2A topic from Agent Card.[/error]")
        console.print("[warning]Please check that the agent is available and its Agent Card is valid.[/warning]")
        console.print(f"[info]Agent name: {getattr(card_obj, 'name', None)!r}[/info]")
        raise SystemExit(2)
    globals()["_a2a_topic"] = a2a_topic_local
    logger.debug(f"main: using a2a_topic={globals()['_a2a_topic']!r}")

    # Create transport early so failures surface before UI interaction
    # Build transport name safely from topic
    topic_for_name = globals()["_a2a_topic"] or TOPIC
    try:
        org, namespace, local_name = topic_for_name.split("/", 2)
    except Exception:
        org, namespace, local_name = TOPIC.split("/", 2)
    transport_name = f"{org}/{namespace}/{local_name}-client"
    logger.debug(f"main: creating SLIM transport endpoint={_endpoint!r} name={transport_name!r}")
    global _transport
    if _transport is None:
        _transport = _factory.create_transport("SLIM", endpoint=_endpoint, name=transport_name)


    # Safely derive UI fields
    agent_name_local = "Agent"
    skills_description_local = ""
    skills_examples_local: list[str] = []
    if card_obj:
        if getattr(card_obj, "name", None):
            agent_name_local = card_obj.name
        try:
            if getattr(card_obj, "skills", None):
                skill = card_obj.skills[0]
                skills_description_local = getattr(skill, "description", "") or ""
                skills_examples_local = getattr(skill, "examples", []) or []
        except Exception:
            pass

    logger.debug(f"main: agent_name_local={agent_name_local!r}, skills_desc_len={len(skills_description_local)}, skills_examples_count={len(skills_examples_local)}")
    # Assign to globals
    globals()["_agent_name"] = agent_name_local
    globals()["_skills_description"] = skills_description_local
    globals()["_skills_examples"] = skills_examples_local

    if not debug:
        console.clear()
    logger.debug(f"main: printing detected banner for agent_name={(_agent_name or 'Agent')!r}")
    print(f"✅ SLIM Agent Card detected for \033[1m\033[32m{_agent_name or 'Agent'}\033[0m")
    asyncio.run(
        run_chat_loop(
            handle_user_input,
            agent_name=_agent_name,
            skills_description=_skills_description,
            skills_examples=_skills_examples,
        )
    )
