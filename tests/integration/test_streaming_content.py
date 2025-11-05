#!/usr/bin/env python3
"""Diagnostic: Check what's in streaming_result artifacts"""
import asyncio
import sys
from uuid import uuid4
import httpx

sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

from a2a.client import A2AClient
from a2a.types import SendStreamingMessageRequest, MessageSendParams

async def check_streaming_content():
    agent_url = "http://localhost:8000"
    query = "show argocd version"

    print("=" * 100)
    print(f"📤 Checking streaming_result content for query: {query}")
    print("=" * 100)
    print()

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

            # Track streaming_result artifacts
            if hasattr(event, 'artifact') and event.artifact:
                artifact_name = event.artifact.name

                if artifact_name == 'streaming_result':
                    if hasattr(event.artifact, 'parts') and event.artifact.parts:
                        for part in event.artifact.parts:
                            text = ""
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                text = part.root.text
                            elif hasattr(part, 'text'):
                                text = part.text
                            
                            if text:
                                streaming_chunks.append(text)
                                # Print first 10 and last 10 chunks
                                if len(streaming_chunks) <= 10 or len(streaming_chunks) % 100 == 0:
                                    print(f"\n📝 EVENT #{event_num}: streaming_result chunk #{len(streaming_chunks)}")
                                    print(f"   Length: {len(text)} chars")
                                    print(f"   Preview: {repr(text[:200])}")

            # Check for completion
            if hasattr(event, 'is_task_complete') and event.is_task_complete:
                print(f"\n🏁 EVENT #{event_num}: TASK COMPLETE")
                break

    print("\n" + "=" * 100)
    print("📊 SUMMARY")
    print("=" * 100)
    print(f"Total events processed: {event_num}")
    print(f"Streaming chunks received: {len(streaming_chunks)}")
    
    if streaming_chunks:
        accumulated_text = "".join(streaming_chunks)
        print(f"Total accumulated length: {len(accumulated_text)} characters")
        print("\n📄 FIRST 500 CHARS:")
        print("-" * 100)
        print(accumulated_text[:500])
        print("-" * 100)
        print("\n📄 LAST 500 CHARS:")
        print("-" * 100)
        print(accumulated_text[-500:])
        print("-" * 100)
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(check_streaming_content())

