# CAIPE CLI

AI-assisted coding, workflows, and platform engineering from the terminal.

CAIPE CLI is a dedicated TypeScript/Bun CLI that connects to a [CAIPE server](https://github.com/cnoe-io/ai-platform-engineering) via the A2A (Agent-to-Agent) or AG-UI streaming protocol. It provides an interactive chat REPL, headless mode for CI/CD pipelines, skill management, and secure credential storage.

## Installation

### Run with npx (no global install)

From npm (after the first `caipe/v*` release is published):

```bash
npx caipe --version
npx caipe config set server.url https://your-caipe-server.example.com
npx caipe auth login
npx caipe chat
```

From GitHub `main` (runs via bundled `tsx`; Node 20+):

```bash
npx github:cnoe-io/agent-chat-cli -- --version
npx github:cnoe-io/agent-chat-cli -- auth login
```

Use `--` before caipe args when using the `github:` specifier.

### Build from source (one-liner)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/cnoe-io/agent-chat-cli/main/setup-caipe-cli.sh)
```

With Grid URL: `CAIPE_SERVER_URL=https://grid.preview.outshift.io bash <(curl -fsSL ...)`

### Released binary (curl installer)

```bash
curl -fsSL https://raw.githubusercontent.com/cnoe-io/agent-chat-cli/main/install.sh | sh
```

Requires a **`caipe/v*.*.*`** GitHub release. Options: `CAIPE_INSTALL_DIR`, `CAIPE_VERSION`.

### npm global

```bash
npm install -g caipe
```

### Git clone + compile

```bash
git clone https://github.com/cnoe-io/agent-chat-cli.git
cd agent-chat-cli
bun install && npm rebuild keytar && npm run compile
./dist/caipe --version
```

## Quick start

```bash
# 1. Point to your CAIPE server
caipe config set server.url https://your-caipe-server.example.com

# 2. Authenticate (opens browser for OAuth)
caipe auth login

# 3. Start chatting
caipe
```

## Commands

| Command | Description |
|---|---|
| `caipe` | Open interactive chat REPL (default) |
| `caipe chat` | Open chat (explicit). Options: `--agent`, `--protocol`, `--headless`, `--resume` |
| `caipe auth login` | Authenticate via OAuth (browser or `--device` flow) |
| `caipe auth logout` | Remove stored credentials |
| `caipe auth status` | Print current auth state |
| `caipe config set <key> <value>` | Set a configuration key |
| `caipe config get <key>` | Print the current value of a key |
| `caipe config unset <key>` | Remove a configuration key |
| `caipe skills list` | List available skills from catalog |
| `caipe skills install <name>` | Install a skill |
| `caipe skills preview <name>` | Display full SKILL.md content |
| `caipe skills update [name]` | Check and update installed skills |
| `caipe agents list` | List available server agents |
| `caipe agents info <name>` | Show agent capabilities |
| `caipe memory` | Manage persistent context files |
| `caipe commit` | DCO-compliant commit with AI attribution |

### Global options

```
--agent <name>    CAIPE server agent to use for this session (default: "default")
--url <url>       Override server.url from settings.json
--no-color        Disable ANSI color output
--json            Machine-readable JSON output (non-interactive commands)
-v, --version     Print version and exit
```

## Interactive chat

The chat REPL provides:

- **Streaming responses** via A2A or AG-UI Server-Sent Events
- **Slash commands** — type `/` for a picker: `/clear`, `/compact`, `/login`, `/skills`, `/agents`, `/help`, `/exit`
- **Readline-style keybindings** — `Ctrl+A/E` (start/end), `Ctrl+B/F` (char movement), `Alt+B/F` (word movement), `Ctrl+U/K/W` (kill line/word), `Ctrl+D` (exit)
- **Input history** — `Up/Down` or `Ctrl+P/N` to cycle through previous inputs
- **Shell pipes** — `!command` runs a shell command and returns output
- **Tool call visualization** — active tool calls displayed in the status footer

### Headless mode

For CI/CD pipelines and scripting:

```bash
# Single prompt
caipe chat --headless --prompt "Explain the deployment architecture"

# From file
caipe chat --headless --prompt-file question.txt --output json

# Multi-turn via stdin
echo -e "Hello\nWhat is A2A?" | caipe chat --headless --interactive-stdin

# With explicit token
caipe chat --headless --token "$JWT" --prompt "status check"
```

## Configuration

Settings are stored in `~/.config/caipe/settings.json`.

| Key | Description | Example |
|---|---|---|
| `server.url` | CAIPE server base URL | `https://caipe.example.com` |
| `auth.url` | OAuth authorization endpoint (auto-discovered if not set) | `https://auth.example.com` |
| `auth.apiKey` | Static API key (alternative to OAuth) | `sk-...` |
| `auth.credential-storage` | Credential backend: `encrypted-file` (default) or `keychain` | `encrypted-file` |

### Credential storage

By default, credentials are stored in `~/.config/caipe/credentials.enc` using AES-256-GCM encryption with a machine-specific key (derived via PBKDF2 from the platform's hardware UUID). This avoids macOS Keychain popups.

To use the OS keychain instead:

```bash
caipe config set auth.credential-storage keychain
```

This requires the optional `keytar` native module (`npm install keytar`).

## Development

```bash
cd cli
bun install                # install dependencies
npm run dev -- chat        # run in development mode (tsx)
npx vitest run             # run unit tests (114 tests)
npm run lint               # lint with Biome
npm run compile            # build single-file binary for current platform
npm run compile:all        # cross-compile for all platforms
```

### Project structure

```
cli/
  src/
    index.ts              # CLI entry point (Commander.js)
    auth/                 # OAuth, keychain, token management
    chat/                 # Repl.tsx (Ink 5 TUI), streaming, pipes
    headless/             # Non-interactive mode
    platform/             # Config, discovery, setup wizard, display
    skills/               # Skill catalog and management
    agents/               # Agent registry
    commit/               # DCO-compliant commit helper
    memory/               # Memory file management
  tests/                  # Vitest test suite
  npm/                    # Platform-specific npm packages (for npm install -g)
  install.sh              # curl installer
  build-binary.mjs        # Node.js SEA build script (alternative to Bun compile)
```

## License

Apache-2.0
