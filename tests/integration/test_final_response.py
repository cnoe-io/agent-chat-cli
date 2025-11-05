#!/usr/bin/env python3
"""Test to see what the final response actually is"""
import asyncio
import sys

sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

# Monkey-patch render_answer to capture what's being rendered
rendered_responses = []

def mock_render_answer(answer, agent_name="Agent"):
    rendered_responses.append({
        'answer': answer,
        'length': len(answer),
        'agent_name': agent_name
    })
    print("\n📝 render_answer CALLED:")
    print(f"   Agent: {agent_name}")
    print(f"   Length: {len(answer)} chars")
    print(f"   First 100 chars: {answer[:100]}")
    print(f"   Contains 'ArgoCD': {'ArgoCD' in answer or 'argocd' in answer.lower()}")
    print(f"   Contains 'Supervisor': {'Supervisor' in answer}")
    print(f"   Contains 'Write_Todos': {'Write_Todos' in answer}")

async def test_final_response():
    print("=" * 100)
    print("Testing what gets passed to render_answer()")
    print("=" * 100)
    print()
    
    # Patch render_answer before importing
    import agent_chat_cli.chat_interface
    agent_chat_cli.chat_interface.render_answer = mock_render_answer
    
    # Now import and run
    from agent_chat_cli.a2a_client import handle_user_input
    
    try:
        await handle_user_input("show argocd version", token=None)
    except Exception as e:
        print(f"⚠️  Exception: {e}")
    
    print("\n" + "=" * 100)
    print("FINAL ANALYSIS")
    print("=" * 100)
    
    if rendered_responses:
        for i, resp in enumerate(rendered_responses, 1):
            print(f"\nResponse #{i}:")
            print(f"  Length: {resp['length']} chars")
            if 'ArgoCD' in resp['answer'] or 'argocd' in resp['answer'].lower():
                print("  ✅ Contains ArgoCD version info")
            if 'Supervisor' in resp['answer'] or 'Write_Todos' in resp['answer']:
                print("  ❌ Contains tool notification text")
            if resp['length'] < 50:
                print("  ⚠️  Very short response")
                print(f"  Full text: {resp['answer']}")
    else:
        print("❌ render_answer was NEVER called!")
    
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(test_final_response())

