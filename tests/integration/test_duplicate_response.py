#!/usr/bin/env python3
"""Unit test to trace the duplicate response issue"""
import asyncio
import sys
from unittest.mock import patch

sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

# Track all render calls
render_calls = []
live_updates = []

def mock_render_answer(answer, agent_name="Agent"):
    render_calls.append({
        'type': 'render_answer',
        'answer': answer[:100] if len(answer) > 100 else answer,
        'full_length': len(answer)
    })
    print(f"📝 render_answer called with {len(answer)} chars: {answer[:50]}...")

def mock_live_update(self, renderable):
    # Extract the content from the renderable
    live_updates.append({
        'type': 'live_update',
        'renderable': str(type(renderable))
    })

async def test_duplicate_response():
    print("=" * 100)
    print("Testing for duplicate response display")
    print("=" * 100)
    print()
    
    # Patch the render_answer function and Live.update
    with patch('agent_chat_cli.a2a_client.render_answer', side_effect=mock_render_answer):
        with patch('rich.live.Live.update', side_effect=mock_live_update):
            # Import after patching
            from agent_chat_cli.a2a_client import handle_user_input
            
            # Run the actual client
            try:
                await handle_user_input("how can you help?", token=None)
            except Exception as e:
                print(f"⚠️  Exception during execution: {e}")
    
    print("\n" + "=" * 100)
    print("ANALYSIS")
    print("=" * 100)
    
    print(f"\n📊 Total render_answer calls: {len(render_calls)}")
    for i, call in enumerate(render_calls, 1):
        print(f"  Call #{i}: {call['full_length']} chars - {call['answer']}")
    
    print(f"\n📊 Total live_update calls: {len(live_updates)}")
    print("  (Live updates are expected during streaming)")
    
    print("\n" + "=" * 100)
    if len(render_calls) > 1:
        print("❌ ISSUE CONFIRMED: render_answer called multiple times!")
        print("   Expected: 1 call")
        print(f"   Actual: {len(render_calls)} calls")
        
        # Check if they're duplicates
        if len(render_calls) >= 2:
            if render_calls[0]['answer'] == render_calls[1]['answer']:
                print("   ⚠️  Calls contain IDENTICAL content (duplicate)")
            else:
                print("   ℹ️  Calls contain DIFFERENT content")
    else:
        print("✅ SUCCESS: render_answer called exactly once")
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(test_duplicate_response())

