#!/usr/bin/env python3
"""
Test script to verify improved JSON filtering handles spaced field names and markdown.
"""

from unittest.mock import patch

def test_spaced_json_filtering():
    """Test filtering with spaced field names as seen in the actual output"""
    
    # Import after sys.path is set up
    from agent_chat_cli.chat_interface import render_answer, _is_structured_agent_response, _extract_content_from_agent_response
    
    print("🧪 Testing improved JSON filtering...")
    
    # Test case: JSON with spaced field names (as seen in actual output)
    spaced_json = '''{ " is _task _complete ": true , " require _user _input ": false , " content ": " The current version of the system is ** v 3 . 7 . 3 ** . Here are the details :\\n \\n - ** Build Date :** 202 5 - 10 - 14 \\n - ** Git Commit :** b ded 09 fe 4 abd 37 cb 98 d 7 fc 81 b 4 c 14 a 6 f 503 4 e 9 ab \\n - ** Git Tag :** v 3 . 7 . 3 \\n - ** Git Tree State :** clean \\n - ** Go Version :** go 1 . 24 . 4 \\n - ** Compiler :** gc \\n - ** Platform :** linux / arm 64 " , " metadata ": null }'''
    
    print("Testing JSON detection...")
    is_detected = _is_structured_agent_response(spaced_json)
    print(f"  Detected as agent JSON: {is_detected}")
    
    if is_detected:
        print("Testing content extraction...")
        extracted_content = _extract_content_from_agent_response(spaced_json)
        print(f"  Extracted content length: {len(extracted_content)}")
        print(f"  First 100 chars: {extracted_content[:100]}...")
        
        # Check if markdown was fixed
        if "**v3.7.3**" in extracted_content or "**v 3.7.3**" in extracted_content:
            print("  ✅ Markdown bold formatting preserved")
        else:
            print("  ❌ Markdown bold formatting issues")
        
        # Check if newlines were fixed
        if "\n\n" in extracted_content:
            print("  ✅ Newlines properly formatted")
        else:
            print("  ❌ Newline formatting issues")
            
        print("\nCleaned content preview:")
        print("-" * 50)
        print(extracted_content[:300] + "..." if len(extracted_content) > 300 else extracted_content)
        print("-" * 50)
        
        # Test render_answer with the spaced JSON
        print("\nTesting render_answer with spaced JSON...")
        with patch('agent_chat_cli.chat_interface.console'):
            with patch('agent_chat_cli.chat_interface.Markdown') as mock_markdown, \
                 patch('agent_chat_cli.chat_interface.Panel'):
                
                render_answer(spaced_json)
                
                if mock_markdown.called:
                    rendered_content = mock_markdown.call_args[0][0]
                    print(f"  ✅ Content rendered (length: {len(rendered_content)})")
                    print(f"  First 100 chars: {rendered_content[:100]}...")
                else:
                    print("  ❌ Content not rendered")
    else:
        print("  ❌ Failed to detect spaced JSON as agent response")

    # Test mixed content (text + JSON)
    print("\n🧪 Testing mixed content filtering...")
    mixed_content = '''The current version of Ar go Work flows is ** v 3 . 7 . 3 ** . Here are the details : - ** Build Date :** 202 5 - 10 - 14 - ** Git Commit :** b ded 09 fe 4 abd 37 cb 98 d 7 fc 81 b 4 c 14 a 6 f 503 4 e 9 ab - ** Git Tag :** v 3 . 7 . 3 - ** Git Tree State :** clean - ** Go Version :** go 1 . 24 . 4 - ** Compiler :** gc - ** Platform :** linux / arm 64 { " is _task _complete ": true , " require _user _input ": false , " content ": " The current version of the system is ** v 3 . 7 . 3 ** . Here are the details :\\n \\n - ** Build Date :** 202 5 - 10 - 14 \\n - ** Git Commit :** b ded 09 fe 4 abd 37 cb 98 d 7 fc 81 b 4 c 14 a 6 f 503 4 e 9 ab \\n - ** Git Tag :** v 3 . 7 . 3 \\n - ** Git Tree State :** clean \\n - ** Go Version :** go 1 . 24 . 4 \\n - ** Compiler :** gc \\n - ** Platform :** linux / arm 64 " , " metadata ": null }'''
    
    with patch('agent_chat_cli.chat_interface.console'):
        with patch('agent_chat_cli.chat_interface.Markdown') as mock_markdown, \
             patch('agent_chat_cli.chat_interface.Panel'):
            
            render_answer(mixed_content)
            
            if mock_markdown.called:
                rendered_content = mock_markdown.call_args[0][0]
                print(f"  ✅ Mixed content handled (length: {len(rendered_content)})")
                print(f"  First 100 chars: {rendered_content[:100]}...")
                
                # Check if JSON was stripped
                if '{ " is _task _complete "' not in rendered_content:
                    print("  ✅ JSON successfully stripped from mixed content")
                else:
                    print("  ❌ JSON still present in rendered content")
            else:
                print("  ❌ Mixed content not rendered")

if __name__ == "__main__":
    print("🚀 Testing improved JSON filtering for spaced field names and markdown")
    print("=" * 70)
    
    try:
        test_spaced_json_filtering()
        print("\n🎉 Improved filtering tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

