# Display Modes Configuration

## Overview

The CLI offers three distinct display modes that control how agent responses are shown. You can customize the experience based on your preferences and use case.

## Display Modes

### Mode 1: Streaming with Auto-Clear (Default)
**Flags:** `--show-streaming --clear-streaming` (default)
**Env:** `A2A_SHOW_STREAMING=true A2A_CLEAR_STREAMING=true`

Shows streaming text in real-time, then **clears it** and replaces with a clean structured panel.

```
🧑‍💻 You: hello
⏳ Waiting for agent... →
Hello! How can I help you today?

[Text clears and is replaced with:]

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Hello! How can I help you today?                       │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

**Best for:**
- ✅ Clean, professional appearance
- ✅ Avoiding duplicate content
- ✅ Demos and screenshots
- ✅ Users who prefer minimal output

**Command:**
```bash
agent-chat-cli a2a  # Default behavior
# or explicitly:
agent-chat-cli a2a --show-streaming --clear-streaming
```

---

### Mode 2: Streaming with Keep (Your Requested Mode)
**Flags:** `--show-streaming --no-clear-streaming`
**Env:** `A2A_SHOW_STREAMING=true A2A_CLEAR_STREAMING=false`

Shows streaming text in real-time and **keeps it**, then adds the structured panel below.

```
🧑‍💻 You: hello
⏳ Waiting for agent... →
Hello! How can I help you today?

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Hello! How can I help you today?                       │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

**Best for:**
- ✅ Seeing the full conversation flow
- ✅ Debugging streaming behavior
- ✅ Users who like seeing progress
- ✅ Long responses where you want immediate feedback
- ✅ Comparing streamed vs final formatting

**Command:**
```bash
agent-chat-cli a2a --no-clear-streaming
# or with env var:
A2A_CLEAR_STREAMING=false agent-chat-cli a2a
```

---

### Mode 3: Panel Only (No Streaming)
**Flags:** `--no-show-streaming`
**Env:** `A2A_SHOW_STREAMING=false`

Waits for complete response, then shows only the structured panel.

```
🧑‍💻 You: hello
⏳ Waiting for agent... →

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Hello! How can I help you today?                       │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

**Best for:**
- ✅ Cleanest output (text appears only once)
- ✅ Slow terminals or screen readers
- ✅ CI/CD pipelines and automation
- ✅ Users who don't want any duplicate content
- ✅ Recording terminal sessions

**Command:**
```bash
agent-chat-cli a2a --no-show-streaming
# or with env var:
A2A_SHOW_STREAMING=false agent-chat-cli a2a
```

---

## Configuration Methods

### Method 1: Command-Line Flags

```bash
# Mode 1: Streaming with auto-clear (default)
agent-chat-cli a2a

# Mode 2: Streaming and keep (your request)
agent-chat-cli a2a --no-clear-streaming

# Mode 3: Panel only
agent-chat-cli a2a --no-show-streaming

# You can also combine with other options
agent-chat-cli a2a --host localhost --port 8000 --no-clear-streaming
```

### Method 2: Environment Variables

```bash
# Mode 1: Streaming with auto-clear
export A2A_SHOW_STREAMING=true
export A2A_CLEAR_STREAMING=true
agent-chat-cli a2a

# Mode 2: Streaming and keep
export A2A_SHOW_STREAMING=true
export A2A_CLEAR_STREAMING=false
agent-chat-cli a2a

# Mode 3: Panel only
export A2A_SHOW_STREAMING=false
agent-chat-cli a2a
```

### Method 3: .env File

Create a `.env` file:

```bash
# .env
A2A_HOST=localhost
A2A_PORT=8000
A2A_SHOW_STREAMING=true
A2A_CLEAR_STREAMING=false  # Keep streamed text
```

Then use:
```bash
export $(cat .env | xargs)
agent-chat-cli a2a
```

## Configuration Precedence

Settings are applied in this order (highest to lowest):

1. **Environment Variables** - `A2A_SHOW_STREAMING`, `A2A_CLEAR_STREAMING`
2. **Command-Line Flags** - `--show-streaming`, `--clear-streaming`
3. **Default Values** - `true` for both

## Comparison Table

| Mode | Streaming Display | Clear Before Panel | Text Appears | Use Case |
|------|------------------|-------------------|--------------|----------|
| **Mode 1** (Default) | ✅ Yes | ✅ Yes | Once (panel only) | Clean, professional |
| **Mode 2** (Requested) | ✅ Yes | ❌ No | Twice (stream + panel) | Full flow visibility |
| **Mode 3** | ❌ No | N/A | Once (panel only) | Minimal, automation |

## Special Cases

### JSON Structured Responses

For responses with metadata (interactive inputs), streaming is automatically suppressed regardless of settings:

```json
{
  "is_task_complete": false,
  "require_user_input": true,
  "content": "Select an action...",
  "metadata": {...}
}
```

**All modes show:**
```
⏳ Waiting for agent... →

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Select an action...                                    │
│                                                         │
╰─────────────────────────────────────────────────────────╯

📝 Would you like to...
```

This ensures clean display of interactive prompts.

### Very Long Responses

For responses with many lines:

- **Mode 1**: Clears all streamed lines efficiently
- **Mode 2**: Shows full stream history + panel (may scroll)
- **Mode 3**: Only shows panel (most compact)

## Examples

### Development Environment

Keep full conversation flow visible:

```bash
export A2A_SHOW_STREAMING=true
export A2A_CLEAR_STREAMING=false
agent-chat-cli a2a --host localhost --port 8000
```

### Production/Demo Environment

Clean output, single appearance:

```bash
export A2A_SHOW_STREAMING=true
export A2A_CLEAR_STREAMING=true
agent-chat-cli a2a --host prod-agent.example.com
```

### CI/CD Pipeline

Minimal output for logs:

```bash
export A2A_SHOW_STREAMING=false
echo "test query" | agent-chat-cli a2a
```

### Quick Testing

Test different modes quickly:

```bash
# Try mode 1 (default)
agent-chat-cli a2a

# Try mode 2 (keep streaming)
agent-chat-cli a2a --no-clear-streaming

# Try mode 3 (panel only)
agent-chat-cli a2a --no-show-streaming
```

## Terminal Compatibility

All modes work with:
- ✅ Modern Linux terminals
- ✅ macOS Terminal and iTerm2
- ✅ Windows Terminal and WSL
- ✅ VS Code integrated terminal

For Mode 1 (auto-clear), requires ANSI escape code support. If your terminal doesn't support this, use Mode 2 or 3.

## Troubleshooting

### Issue: Text is cleared but panel doesn't appear

**Possible Cause:** Terminal too narrow for panel.

**Solution:** Increase terminal width or use `--no-clear-streaming`.

### Issue: Streaming text appears garbled

**Possible Cause:** Terminal doesn't support real-time updates well.

**Solution:** Use Mode 3 (panel only):
```bash
agent-chat-cli a2a --no-show-streaming
```

### Issue: Want to see streaming but not the panel

**Note:** This is not currently supported. You can only have:
- Streaming + Panel (with or without clear)
- Panel only

### Issue: Lines not clearing properly

**Possible Cause:** Terminal width detection issue or long wrapped lines.

**Solution:** Use Mode 2 to keep streamed text:
```bash
agent-chat-cli a2a --no-clear-streaming
```

## Quick Reference

```bash
# Default - Clean, streaming with auto-clear
agent-chat-cli a2a

# Keep streaming visible (your request)
agent-chat-cli a2a --no-clear-streaming

# Panel only, no streaming
agent-chat-cli a2a --no-show-streaming

# Environment variable approach
A2A_CLEAR_STREAMING=false agent-chat-cli a2a
```

## Summary

Your requested mode is **Mode 2**: Streaming with Keep

**Command:** `agent-chat-cli a2a --no-clear-streaming`
**Env Var:** `A2A_CLEAR_STREAMING=false`

This will:
- ✅ Show streaming text as it arrives
- ✅ Keep the streamed text visible
- ✅ Add the "AI Platform Engineer Response" panel below
- ✅ Provide full visibility of the conversation flow




