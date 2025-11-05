#!/usr/bin/env python3
"""Run a single query and capture all output including debug statements"""
import subprocess

# Set up the command
cmd = """
cd /Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli
rm -rf agent_chat_cli/__pycache__
find . -name "*.pyc" -delete 2>/dev/null || true
source .venv/bin/activate
export A2A_HOST=localhost
export A2A_PORT=8000
export A2A_TOKEN=foo
echo "show argocd version" | python -m agent_chat_cli a2a --debug 2>&1
"""

print("=" * 100)
print("Running CLI query with debug output...")
print("=" * 100)
print()

result = subprocess.run(
    ["bash", "-c", cmd],
    capture_output=True,
    text=True,
    timeout=120
)

output = result.stdout + result.stderr

# Save full output
with open("/tmp/full_cli_output.txt", "w") as f:
    f.write(output)

print(output)

print("\n" + "=" * 100)
print("ANALYSIS")
print("=" * 100)

# Check for debug output
if "🔍 DEBUG:" in output:
    print("✅ DEBUG output found!")
    debug_lines = [line for line in output.split('\n') if '🔍 DEBUG:' in line]
    for line in debug_lines:
        print(f"  {line}")
else:
    print("❌ No DEBUG output found - code changes not loaded!")

# Check final response
if "Ai platform engineer Response" in output:
    print("\n✅ Final response panel found")
    lines = output.split('\n')
    in_panel = False
    panel_content = []
    for line in lines:
        if "Ai platform engineer Response" in line:
            in_panel = True
            continue
        if in_panel:
            if line.strip().startswith('╰') or (line.strip().startswith('💬') and 'You:' in line):
                break
            panel_content.append(line)
    
    content = '\n'.join(panel_content).strip()
    print(f"  Content length: {len(content)} chars")
    if "ArgoCD" in content or "argocd" in content.lower():
        print("  ✅ Contains ArgoCD version info")
    if "Supervisor" in content or "Write_Todos" in content:
        print("  ❌ Contains tool notification")
    print(f"  First 100 chars: {content[:100]}")

print("\n" + "=" * 100)
print("Full output saved to: /tmp/full_cli_output.txt")
print("=" * 100)

