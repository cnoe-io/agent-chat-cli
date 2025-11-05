#!/usr/bin/env python3
"""Test the CLI to verify final response display"""
import subprocess

def test_cli_response():
    print("=" * 100)
    print("Testing CLI final response display")
    print("=" * 100)
    print()

    # Run the CLI with the query
    cmd = [
        "bash", "-c",
        'cd /Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli && '
        'source .venv/bin/activate && '
        'echo "show argocd version" | timeout 60 python -m agent_chat_cli --agent-url http://localhost:8000'
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=70
        )

        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print("\nReturn code:", result.returncode)

        # Check if the response contains the expected version info
        if "v3.1.8" in result.stdout and "Ai platform engineer Response" in result.stdout:
            # Check if the response panel has version info or just tool notifications
            lines = result.stdout.split('\n')
            in_response_panel = False
            response_content = []

            for line in lines:
                if "Ai platform engineer Response" in line:
                    in_response_panel = True
                    continue
                if in_response_panel:
                    if line.strip().startswith('╰') or line.strip().startswith('💬'):
                        break
                    response_content.append(line)

            response_text = '\n'.join(response_content)
            print("\n" + "=" * 100)
            print("EXTRACTED RESPONSE PANEL CONTENT:")
            print("=" * 100)
            print(response_text)
            print("=" * 100)

            if "v3.1.8" in response_text:
                print("\n✅ SUCCESS: Response panel contains version information!")
                return True
            elif "Calling Agent" in response_text or "tool" in response_text.lower():
                print("\n❌ FAILURE: Response panel contains tool notifications instead of version info!")
                return False
            else:
                print("\n⚠️  WARNING: Response panel content unclear")
                return False
        else:
            print("\n❌ FAILURE: Expected content not found in output")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ FAILURE: Command timed out")
        return False
    except Exception as e:
        print(f"\n❌ FAILURE: {e}")
        return False

if __name__ == "__main__":
    success = test_cli_response()
    exit(0 if success else 1)

