#!/usr/bin/env python3
"""Test that partial_result is correctly displayed in the UI"""
import asyncio
import sys
from uuid import uuid4
import httpx

sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

from a2a.client import A2AClient
from a2a.types import SendStreamingMessageRequest, MessageSendParams

async def test_partial_result_display():
    agent_url = "http://localhost:8000"
    query = "show argocd version"

    print("=" * 100)
    print(f"📤 Testing partial_result display for query: {query}")
    print("=" * 100)
    print()

    partial_result_found = False
    partial_result_text = ""
    streaming_chunks = []

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

                if artifact_name == 'partial_result':
                    partial_result_found = True
                    print(f"\n✅ EVENT #{event_num}: partial_result found!")
                    print(f"🔍 DEBUG: artifact type: {type(event.artifact)}")
                    print(f"🔍 DEBUG: artifact dict: {event.artifact.__dict__ if hasattr(event.artifact, '__dict__') else 'N/A'}")
                    print(f"🔍 DEBUG: hasattr parts: {hasattr(event.artifact, 'parts')}")
                    if hasattr(event.artifact, 'parts'):
                        print(f"🔍 DEBUG: parts: {event.artifact.parts}")
                        print(f"🔍 DEBUG: parts type: {type(event.artifact.parts)}")
                    # Extract text from the artifact
                    if hasattr(event.artifact, 'parts') and event.artifact.parts:
                        for idx, part in enumerate(event.artifact.parts):
                            print(f"🔍 DEBUG: part[{idx}] type: {type(part)}")
                            print(f"🔍 DEBUG: part[{idx}] dict: {part.__dict__ if hasattr(part, '__dict__') else 'N/A'}")
                            # Part objects have a 'root' attribute containing the TextPart
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                print(f"🔍 DEBUG: part[{idx}] text length: {len(part.root.text)}")
                                partial_result_text += part.root.text
                            elif hasattr(part, 'text'):
                                print(f"🔍 DEBUG: part[{idx}] text length: {len(part.text)}")
                                partial_result_text += part.text
                    print(f"📝 Content length: {len(partial_result_text)} characters")
                    print("\n--- PARTIAL RESULT CONTENT ---")
                    print(partial_result_text)
                    print("--- END PARTIAL RESULT ---\n")

                elif artifact_name == 'streaming_result':
                    if hasattr(event.artifact, 'parts') and event.artifact.parts:
                        for part in event.artifact.parts:
                            # Part objects have a 'root' attribute containing the TextPart
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                streaming_chunks.append(part.root.text)
                            elif hasattr(part, 'text'):
                                streaming_chunks.append(part.text)
                    # Show a sample of streaming results
                    if len(streaming_chunks) <= 5 or len(streaming_chunks) % 100 == 0:
                        print(f"  📝 EVENT #{event_num}: streaming_result #{len(streaming_chunks)}")

            # Check for completion
            if hasattr(event, 'is_task_complete') and event.is_task_complete:
                print(f"\n🏁 EVENT #{event_num}: TASK COMPLETE")
                break

    print("\n" + "=" * 100)
    print("📊 SUMMARY")
    print("=" * 100)
    print(f"Total events processed: {event_num}")
    print(f"Partial result found: {'✅ YES' if partial_result_found else '❌ NO'}")
    if partial_result_found:
        print(f"Partial result length: {len(partial_result_text)} characters")
        print("\n📄 EXPECTED FINAL DISPLAY:")
        print("-" * 100)
        print(partial_result_text)
        print("-" * 100)
    print(f"\nStreaming chunks received: {len(streaming_chunks)}")
    if streaming_chunks:
        accumulated_text = "".join(streaming_chunks)
        print(f"Accumulated streaming text length: {len(accumulated_text)} characters")
        print("\n📄 ACCUMULATED STREAMING OUTPUT:")
        print("-" * 100)
        print(accumulated_text[:500] + ("..." if len(accumulated_text) > 500 else ""))
        print("-" * 100)
    print("=" * 100)

    return partial_result_found, partial_result_text

if __name__ == "__main__":
    found, text = asyncio.run(test_partial_result_display())
    if not found:
        print("\n❌ TEST FAILED: No partial_result artifact found!")
        sys.exit(1)
    if not text or len(text) < 10:
        print("\n❌ TEST FAILED: Partial result is empty or too short!")
        sys.exit(1)
    print("\n✅ TEST PASSED: Partial result found and contains content!")
    sys.exit(0)

