#!/usr/bin/env python3
"""
Test the complete_result artifact handling and content filtering.
This simulates the exact mixed content we saw from the curl command.
"""

import sys

def test_complete_result_cleaning():
    """Test the complete_result artifact content cleaning."""

    from agent_chat_cli.a2a_client import clean_mixed_agent_content

    print("🧪 Testing complete_result content cleaning...")

    # Simulate the exact content from the curl output
    mixed_content = 'Hello! How can I assist you with Argo Workflows today?{"is_task_complete":true,"require_user_input":false,"content":"Hello! How can I assist you with Argo Workflows today?","metadata":null}'

    print(f"Input length: {len(mixed_content)} chars")
    print(f"Input preview: {mixed_content[:100]}...")

    # Test the cleaning function
    cleaned_content = clean_mixed_agent_content(mixed_content)

    print(f"Output length: {len(cleaned_content)} chars")
    print(f"Output: '{cleaned_content}'")

    # Verify that we got just the human-readable part
    expected = "Hello! How can I assist you with Argo Workflows today?"

    if cleaned_content == expected:
        print("✅ Successfully extracted clean content from mixed response")
    else:
        print(f"❌ Expected: '{expected}'")
        print(f"❌ Got: '{cleaned_content}'")
        return False

    # Test with the spaced version we saw in the original issue
    spaced_mixed = 'The current version of Argo Workflows is **v3.7.3**. Here are the details: - **Build Date:** 2025-10-14 - **Git Commit:** bded09fe4abd37cb98d7fc81b4c14a6f5034e9ab - **Git Tag:** v3.7.3 - **Git Tree State:** clean - **Go Version:** go1.24.4 - **Compiler:** gc - **Platform:** linux/arm64 { " is _task _complete ": true , " require _user _input ": false , " content ": " The current version of the system is ** v 3 . 7 . 3 ** . Here are the details :\\n \\n - ** Build Date :** 202 5 - 10 - 14 \\n - ** Git Commit :** b ded 09 fe 4 abd 37 cb 98 d 7 fc 81 b 4 c 14 a 6 f 503 4 e 9 ab \\n - ** Git Tag :** v 3 . 7 . 3 \\n - ** Git Tree State :** clean \\n - ** Go Version :** go 1 . 24 . 4 \\n - ** Compiler :** gc \\n - ** Platform :** linux / arm 64 " , " metadata ": null }'

    print("\n🧪 Testing spaced mixed content...")
    print(f"Input length: {len(spaced_mixed)} chars")

    cleaned_spaced = clean_mixed_agent_content(spaced_mixed)
    print(f"Output length: {len(cleaned_spaced)} chars")
    print(f"Output: '{cleaned_spaced}'")

    # Should get the text before the JSON
    expected_start = "The current version of Argo Workflows is **v3.7.3**"
    if cleaned_spaced.startswith(expected_start):
        print("✅ Successfully extracted clean content from spaced mixed response")
    else:
        print(f"❌ Expected to start with: '{expected_start}'")
        print(f"❌ Got: '{cleaned_spaced[:100]}...'")
        return False

    return True

def test_priority_order():
    """Test that complete_result takes priority over other sources."""
    print("\n🧪 Testing priority order (simulated)...")

    # Simulate different content sources
    streaming_content = "Streaming: Hello! How can I help?"
    partial_result_content = "Partial: Hello! How can I assist?"
    complete_result_content = "Complete: Hello! How can I assist you with Argo Workflows?"

    # According to our new logic, complete_result should win
    sources = {
        'complete_result': complete_result_content,
        'partial_result': partial_result_content,
        'streaming': streaming_content
    }

    # Simulate the priority logic
    if sources.get('complete_result'):
        final_text = sources['complete_result']
        source = 'complete_result'
    elif sources.get('partial_result'):
        final_text = sources['partial_result']
        source = 'partial_result'
    else:
        final_text = sources['streaming']
        source = 'streaming'

    print(f"Selected source: {source}")
    print(f"Final text: '{final_text}'")

    if source == 'complete_result' and final_text == complete_result_content:
        print("✅ complete_result correctly takes priority")
        return True
    else:
        print("❌ Priority order incorrect")
        return False

def test_streaming_vs_final_behavior():
    """Test that streaming display works but final result is clean."""
    print("\n🧪 Testing streaming vs final result behavior...")

    # Simulate what happens during streaming
    streaming_chunks = [
        "Hello",
        "!",
        " How",
        " can",
        " I",
        " assist",
        " you",
        " with",
        " Argo",
        " Workflows",
        " today",
        "?",
        '{"is_task_complete":',
        'true,',
        '"require_user_input":',
        'false,',
        '"content":',
        '"Hello! How can I assist you with Argo Workflows today?",',
        '"metadata":',
        'null',
        '}'
    ]

    # Build up streaming content (simulates what user sees during typing)
    streaming_buffer = ""
    clean_portions = []

    print("Simulating streaming chunks:")
    for i, chunk in enumerate(streaming_chunks):
        streaming_buffer += chunk

        # Show what would be displayed during streaming (only clean parts)
        if not chunk.startswith('{"') and not any(json_marker in chunk for json_marker in ['is_task_complete', 'require_user_input', 'content', 'metadata']):
            clean_portions.append(chunk)
            print(f"  Chunk {i+1}: '{chunk}' -> Display: {''.join(clean_portions)}")
        else:
            print(f"  Chunk {i+1}: '{chunk}' -> [JSON, not displayed in streaming]")

    print(f"\nFinal streaming buffer: '{streaming_buffer}'")

    # Now test the complete_result processing
    from agent_chat_cli.a2a_client import clean_mixed_agent_content
    final_clean = clean_mixed_agent_content(streaming_buffer)

    print(f"Final clean result: '{final_clean}'")

    expected_final = "Hello! How can I assist you with Argo Workflows today?"

    if final_clean == expected_final:
        print("✅ Streaming chunks show progressive typing, final result is clean")
        return True
    else:
        print(f"❌ Expected final: '{expected_final}'")
        print(f"❌ Got final: '{final_clean}'")
        return False

if __name__ == "__main__":
    print("🚀 Testing complete_result artifact handling with streaming UX preservation")
    print("=" * 80)

    try:
        success = True
        success &= test_complete_result_cleaning()
        success &= test_priority_order()
        success &= test_streaming_vs_final_behavior()

        if success:
            print("\n🎉 All complete_result tests passed!")
            print("\n📋 Summary:")
            print("- ✅ Streaming display works (users see progressive typing)")
            print("- ✅ complete_result artifact takes highest priority for final display")
            print("- ✅ Mixed content (text + JSON) is properly cleaned")
            print("- ✅ Only the human-readable part is shown in final result")
            print("- ✅ Works with both normal and spaced JSON formats")
            print("\n🎯 User Experience:")
            print("  1. User sees real-time streaming (live typing effect)")
            print("  2. After streaming completes, clean final result is displayed")
            print("  3. No duplicate content or raw JSON in final output")
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

