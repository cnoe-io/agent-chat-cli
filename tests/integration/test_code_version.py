#!/usr/bin/env python3
"""Test to verify which version of the code is actually loaded"""
import sys
sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

print("=" * 100)
print("CODE VERSION CHECK")
print("=" * 100)

# Check 1: Version number
try:
    from agent_chat_cli.__main__ import __version__
    print(f"✅ CLI Version: {__version__}")
except Exception as e:
    print(f"❌ Could not get version: {e}")

# Check 2: Check if the key fix is present (line 724)
try:
    import inspect
    from agent_chat_cli import a2a_client
    source = inspect.getsource(a2a_client.handle_user_input)

    # Look for the specific line we added
    if "if text and artifact_name:" in source:
        print("✅ Fix 1 present: 'if text and artifact_name:' found (status messages excluded)")
    else:
        print("❌ Fix 1 missing: Old code - status messages NOT excluded")

    # Look for final_response_text
    if "final_response_text" in source:
        print("✅ Fix 2 present: 'final_response_text' variable found (separate from response_markdown)")
    else:
        print("❌ Fix 2 missing: Old code - using response_markdown directly")

    # Look for smart space insertion
    if "not clean_streaming_text.startswith" in source:
        print("✅ Fix 3 present: Smart space insertion logic found")
    else:
        print("❌ Fix 3 missing: Old code - no smart spacing")

    # Check update_live simplification
    if "last_panel_state" in source:
        print("❌ Fix 4 NOT applied: Still using memoization (last_panel_state exists)")
    else:
        print("✅ Fix 4 present: Memoization removed from update_live")

except Exception as e:
    print(f"❌ Could not check code: {e}")

print("=" * 100)
print("\nIf any fixes show as MISSING, the code changes haven't been loaded.")
print("Try: rm -rf agent_chat_cli/__pycache__ && python -m agent_chat_cli")
print("=" * 100)

