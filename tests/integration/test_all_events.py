#!/usr/bin/env python3
import asyncio
import sys
from uuid import uuid4
import httpx

try:
    import pytest
    pytestmark = pytest.mark.skip("diagnostic script; use via __main__ only")
except ImportError:
    pytestmark = None

sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

from a2a.client import A2AClient
from a2a.types import SendStreamingMessageRequest, MessageSendParams

async def test_streaming():
    agent_url = "http://localhost:8000"
    query = "show all pagerduty services and who is on call"

    print("=" * 100)
    print(f"📤 QUERY: {query}")
    print("=" * 100)
    print()

    event_num = 0
    artifact_counts = {}
    exec_plan_artifacts = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
        print(f"✅ Connecting to {agent_url}...")
        client = await A2AClient.get_client_from_agent_card_url(httpx_client, agent_url)
        client.url = agent_url
        print("✅ Connected!")
        print()

        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": query}],
                "messageId": uuid4().hex,
                "contextId": uuid4().hex
            }
        }

        streaming_request = SendStreamingMessageRequest(
            id=uuid4().hex,
            params=MessageSendParams(**payload),
        )

        print("📡 Streaming events:")
        print("-" * 100)

        async for chunk in client.send_message_streaming(streaming_request):
            event_num += 1
            event = chunk.root.result

            # Track artifacts
            if hasattr(event, 'artifact') and event.artifact:
                artifact_name = event.artifact.name
                artifact_counts[artifact_name] = artifact_counts.get(artifact_name, 0) + 1

                # Capture execution plan artifacts
                if 'execution_plan' in artifact_name or 'write_todos' in artifact_name.lower():
                    artifact_text = getattr(event.artifact, 'text', '')
                    exec_plan_artifacts.append({
                        'event_num': event_num,
                        'name': artifact_name,
                        'text': artifact_text
                    })
                    print(f"\n{'='*100}")
                    print(f"🎯 EVENT #{event_num}: {artifact_name.upper()}")
                    print(f"{'='*100}")
                    print(artifact_text)
                    print(f"{'='*100}\n")

            # Check for completion
            if hasattr(event, 'is_task_complete') and event.is_task_complete:
                print(f"\n🏁 EVENT #{event_num}: TASK COMPLETE")
                break

    print("\n" + "=" * 100)
    print("📊 SUMMARY")
    print("=" * 100)
    print(f"Total events: {event_num}")
    print("\nArtifact counts:")
    for name, count in sorted(artifact_counts.items()):
        marker = "🎯" if 'execution_plan' in name else "📦"
        print(f"  {marker} {name}: {count}")

    print(f"\nExecution plan artifacts found: {len(exec_plan_artifacts)}")
    if not exec_plan_artifacts:
        print("  ❌ NO execution_plan_update or execution_plan_status_update found!")
        print("  ❌ Agent may not be calling write_todos or prompt not loaded")

    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(test_streaming())
