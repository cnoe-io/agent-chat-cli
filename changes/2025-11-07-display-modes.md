# Display Modes for Agent Output

**Status**: 🟢 In-use
**Category**: Features & Enhancements
**Date**: November 7, 2025

## Overview

The CLI offers three distinct display modes that control how agent responses are shown, providing flexibility for different use cases from interactive development to automated pipelines.

## The Problem

Users have different needs when viewing agent responses:

1. **Demo/Production users** want clean, professional output without duplicate content
2. **Developers** need to see the full conversation flow including streaming progress
3. **Automation/CI** requires minimal output for logging
4. **Screen reader users** need output that doesn't confuse assistive technology
5. **Debugging** scenarios require visibility into streaming behavior

Previously, there was only one display mode with no configuration options.

## The Solution

Three configurable display modes accessible via command-line flags or environment variables:

### Mode 1: Streaming with Auto-Clear (Default)
Shows streaming text in real-time, then **clears it** and replaces with a clean structured panel.

### Mode 2: Streaming with Keep
Shows streaming text in real-time and **keeps it**, then adds the structured panel below.

### Mode 3: Panel Only (No Streaming)
Waits for complete response, then shows only the structured panel.

## How It Works

### Mode 1: Streaming with Auto-Clear (Default)

**Flags:** `--show-streaming --clear-streaming` (default)  
**Env:** `A2A_SHOW_STREAMING=true A2A_CLEAR_STREAMING=true`

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
```

---

### Mode 2: Streaming with Keep

**Flags:** `--show-streaming --no-clear-streaming`  
**Env:** `A2A_SHOW_STREAMING=true A2A_CLEAR_STREAMING=false`

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

**Command:**
```bash
agent-chat-cli a2a --no-clear-streaming
```

---

### Mode 3: Panel Only (No Streaming)

**Flags:** `--no-show-streaming`  
**Env:** `A2A_SHOW_STREAMING=false`

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
- ✅ Recording terminal sessions

**Command:**
```bash
agent-chat-cli a2a --no-show-streaming
```

## Configuration

### Method 1: Command-Line Flags

```bash
# Mode 1: Streaming with auto-clear (default)
agent-chat-cli a2a

# Mode 2: Streaming and keep
agent-chat-cli a2a --no-clear-streaming

# Mode 3: Panel only
agent-chat-cli a2a --no-show-streaming
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

### Configuration Precedence

Settings are applied in this order (highest to lowest):

1. **Environment Variables** - `A2A_SHOW_STREAMING`, `A2A_CLEAR_STREAMING`
2. **Command-Line Flags** - `--show-streaming`, `--clear-streaming`
3. **Default Values** - `true` for both

## Features

### Special Cases

**JSON Structured Responses:**  
For responses with metadata (interactive inputs), streaming is automatically suppressed regardless of settings to ensure clean display of interactive prompts.

**Very Long Responses:**
- **Mode 1**: Clears all streamed lines efficiently
- **Mode 2**: Shows full stream history + panel (may scroll)
- **Mode 3**: Only shows panel (most compact)

### Comparison Table

| Mode | Streaming Display | Clear Before Panel | Text Appears | Use Case |
|------|------------------|-------------------|--------------|----------|
| **Mode 1** (Default) | ✅ Yes | ✅ Yes | Once (panel only) | Clean, professional |
| **Mode 2** | ✅ Yes | ❌ No | Twice (stream + panel) | Full flow visibility |
| **Mode 3** | ❌ No | N/A | Once (panel only) | Minimal, automation |

## Implementation Files

**Modified Files:**

1. **`agent_chat_cli/__main__.py`**
   - Added `--show-streaming/--no-show-streaming` CLI flags
   - Added `--clear-streaming/--no-clear-streaming` CLI flags
   - Environment variable integration

2. **`agent_chat_cli/a2a_client.py`**
   - Added `SHOW_STREAMING` and `CLEAR_STREAMING` configuration
   - Implemented line tracking and clearing logic
   - Terminal width-aware line counting
   - ANSI escape code support for clearing

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

## Terminal Compatibility

All modes work with:
- ✅ Modern Linux terminals
- ✅ macOS Terminal and iTerm2
- ✅ Windows Terminal and WSL
- ✅ VS Code integrated terminal

For Mode 1 (auto-clear), requires ANSI escape code support. If your terminal doesn't support this, use Mode 2 or 3.

## Benefits

### 1. Flexibility
Three distinct modes for different scenarios - development, production, automation.

### 2. User Control
Users can choose their preferred experience via simple flags or environment variables.

### 3. Professional Output
Mode 1 provides clean, demo-ready output without duplicate content.

### 4. Developer Experience
Mode 2 shows full streaming progress for debugging and development.

### 5. Automation Friendly
Mode 3 provides minimal, clean output perfect for CI/CD pipelines.

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

# Keep streaming visible
agent-chat-cli a2a --no-clear-streaming

# Panel only, no streaming
agent-chat-cli a2a --no-show-streaming

# Environment variable approach
A2A_CLEAR_STREAMING=false agent-chat-cli a2a
```

---

**This provides users with flexible display options for any use case!** 🎨

