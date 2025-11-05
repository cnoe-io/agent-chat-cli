#!/usr/bin/env python3
"""Comprehensive debugging of the streaming flow"""
import asyncio
import sys
from uuid import uuid4
import httpx

sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

from a2a.client import A2AClient
from a2a.types import SendStreamingMessageRequest, MessageSendParams

async def trace_streaming_flow():
    agent_url = "http://localhost:8000"
    query = "show argocd version"

    print("=" * 100)
    print(f"📤 COMPREHENSIVE DEBUG: {query}")
    print("=" * 100)
    print()

    artifact_counts = {}
    tool_notifications = []
    streaming_chunks = []
    partial_result_content = None

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

        print("📡 Processing events...")
        event_num = 0

        async for chunk in client.send_message_streaming(streaming_request):
            event_num += 1
            event = chunk.root.result

            # Track artifacts
            if hasattr(event, 'artifact') and event.artifact:
                artifact_name = event.artifact.name
                artifact_counts[artifact_name] = artifact_counts.get(artifact_name, 0) + 1

                # Extract text
                text = ""
                if hasattr(event.artifact, 'parts') and event.artifact.parts:
                    for part in event.artifact.parts:
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            text = part.root.text
                        elif hasattr(part, 'text'):
                            text = part.text

                if artifact_name == 'tool_notification_start' and text:
                    tool_notifications.append(f"START: {text[:80]}")
                    if artifact_counts[artifact_name] <= 3:
                        print(f"  🔧 EVENT #{event_num}: tool_notification_start: {text[:80]}")

                elif artifact_name == 'tool_notification_end' and text:
                    tool_notifications.append(f"END: {text[:80]}")
                    if artifact_counts[artifact_name] <= 3:
                        print(f"  ✅ EVENT #{event_num}: tool_notification_end: {text[:80]}")

                elif artifact_name == 'streaming_result' and text:
                    streaming_chunks.append(text)
                    if len(streaming_chunks) <= 3 or len(streaming_chunks) % 100 == 0:
                        print(f"  📝 EVENT #{event_num}: streaming_result #{len(streaming_chunks)}: len={len(text)}, preview={repr(text[:50])}")

                elif artifact_name == 'partial_result':
                    partial_result_content = text
                    print(f"\n  ⭐ EVENT #{event_num}: partial_result found!")
                    print(f"     Length: {len(text)} chars")
                    print(f"     First 100 chars: {repr(text[:100])}")
                    print(f"     Last 100 chars: {repr(text[-100:])}")

            # Check for completion
            if hasattr(event, 'is_task_complete') and event.is_task_complete:
                print(f"\n🏁 EVENT #{event_num}: TASK COMPLETE")
                break

    print("\n" + "=" * 100)
    print("📊 ARTIFACT SUMMARY")
    print("=" * 100)
    for artifact, count in sorted(artifact_counts.items()):
        print(f"  {artifact}: {count} events")

    print("\n" + "=" * 100)
    print("🔧 TOOL NOTIFICATIONS")
    print("=" * 100)
    print(f"  Total: {len(tool_notifications)}")
    for notif in tool_notifications[:5]:
        print(f"  - {notif}")
    if len(tool_notifications) > 5:
        print(f"  ... and {len(tool_notifications) - 5} more")

    print("\n" + "=" * 100)
    print("📝 STREAMING CHUNKS")
    print("=" * 100)
    print(f"  Total chunks: {len(streaming_chunks)}")
    if streaming_chunks:
        accumulated = "".join(streaming_chunks)
        print(f"  Accumulated length: {len(accumulated)} chars")
        print(f"  First 200 chars: {repr(accumulated[:200])}")
        print(f"  Last 200 chars: {repr(accumulated[-200:])}")

    print("\n" + "=" * 100)
    print("⭐ PARTIAL RESULT")
    print("=" * 100)
    if partial_result_content:
        print(f"  Length: {len(partial_result_content)} chars")
        print(f"  Content:\n{partial_result_content}")
    else:
        print("  ❌ No partial_result received!")

    print("\n" + "=" * 100)
    print("🔍 ANALYSIS")
    print("=" * 100)

    # Check if tool notifications might be in streaming chunks
    if streaming_chunks:
        sample_chunks = streaming_chunks[:10]
        has_tool_notif = any("Supervisor" in chunk or "Calling" in chunk for chunk in sample_chunks)
        if has_tool_notif:
            print("  ⚠️  WARNING: Tool notification text found in streaming_result chunks!")
            print("  This means tool notifications are leaking into the streaming buffer.")
        else:
            print("  ✅ Streaming chunks look clean (no tool notification text)")

    # Check streaming chunk sizes
    if streaming_chunks:
        chunk_sizes = [len(c) for c in streaming_chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        print(f"  Average chunk size: {avg_size:.1f} chars")
        if avg_size < 2:
            print("  ⚠️  WARNING: Very small chunks (character-by-character streaming)")

    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(trace_streaming_flow())

