from typing import Any, Union, Optional
import asyncio
import json
import logging
import os
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
logger = logging.getLogger("slim_client")

_factory: AgntcyFactory = AgntcyFactory()
_transport: Any = None
_client: Any = None
_agent_name: str = "Agent"
_skills_description: str = ""
_skills_examples: list[str] = []
_endpoint: Optional[str] = None
_remote_card_raw: Optional[Union[str, AgentCard, dict]] = None
_remote_card_card: Optional[AgentCard] = None


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


def _compute_routable_name(subject: Union[AgentCard, dict, str]) -> str:
    # Derive org/namespace/local_name from the best available info
    org = "cnoe"  # default org; override via env if provided
    namespace = "agents"  # default namespace
    local = "agent"  # default local name

    # Allow environment overrides
    org = os.environ.get("SLIM_ORG", org)
    namespace = os.environ.get("SLIM_NAMESPACE", namespace)

    # Prefer AgentCard.name for local; else dict["name"]; else last token of string/URL
    if isinstance(subject, AgentCard):
        local = getattr(subject, "name", None) or local
    elif isinstance(subject, dict):
        local = subject.get("name") or local
    else:
        s = str(subject).strip()
        if s.startswith(("http://", "https://")):
            local = s.rstrip("/").rsplit("/", 1)[-1] or local
        elif s:
            local = s

    # Sanitize local to avoid spaces and illegal chars
    local = str(local).strip().replace(" ", "-").replace("/", "-")
    # Ensure non-empty components
    org = org or "cnoe"
    namespace = namespace or "agents"
    local = local or "agent"
    # Allow full override if provided
    override = os.environ.get("SLIM_ROUTABLE_NAME")
    if override:
        return override
    return f"{org}/{namespace}/{local}"


async def _ensure_client():
    """Ensure A2A client exists; transport is created in main()."""
    global _client
    logger.debug(f"_ensure_client: _client is {'present' if _client else 'None'}")
    if _client is not None:
        return

    subject = _remote_card_card or _remote_card_raw
    logger.debug(f"_ensure_client: subject type={type(subject)}, subject preview={str(subject)[:200]}")
    if isinstance(subject, AgentCard):
        topic = "default/default/agent-slim"
        # logger.debug(f"_ensure_client: created A2A topic via SDK from AgentCard: {topic}")
    else:
        topic = "default/default/agent-slim"
        logger.warning("_ensure_client: non-AgentCard subject provided; building topic locally to avoid SDK .name access")
        logger.debug(f"_ensure_client: created A2A topic locally from non-card subject: {topic}")

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

        trace_id = os.environ.get("CNOE_TRACE_ID")
        if not trace_id:
            try:
                from cnoe_agent_utils.tracing import TracingManager

                tracing = TracingManager()
                trace_id = tracing.get_trace_id() if tracing.is_enabled else None
            except Exception:
                trace_id = None
        if trace_id:
            msg_kwargs["metadata"] = {"trace_id": trace_id}

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
        logger.exception(f"handle_user_input: exception while sending/rendering")
        render_answer(f"❌ Error sending message: {e}", agent_name=_agent_name or "Agent")


def main(endpoint: str, remote_card: str, debug: bool = False):
    """CLI entry point for the SLIM client."""
    global _endpoint, _remote_card_raw, _agent_name, _skills_description, _skills_examples
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
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

    # Create transport early so failures surface before UI interaction
    subject_for_name = globals().get("_remote_card_card") or _remote_card_raw or "agent"
    routable_name = _compute_routable_name(subject_for_name)
    logger.debug(f"main: creating SLIM transport endpoint={_endpoint!r} name={routable_name!r}")
    global _transport
    if _transport is None:
        _transport = _factory.create_transport("SLIM", endpoint=_endpoint, name="default/default/agent-slim-client")


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
