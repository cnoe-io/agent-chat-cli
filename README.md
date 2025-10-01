# Welcome to the A2A CLI - Agentic Chat Client 🤖💬

### **🚀 A Lightweight and fast command-line chat interface.**

[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

[![Docker Build and Push](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/docker-build-publish.yml/badge.svg)](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/docker-build-publish.yml) [![Ruff Linter](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/lint.yml/badge.svg)](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/lint.yml) [![Conventional Commits](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/conventional_commits.yml/badge.svg)](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/conventional_commits.yml)

## ✨ Features

- 🔌 Easy integration with A2A
- 🔗 Read and render A2A card on launch
- 🔒 Support passing OAuth2 Bearer Token or Shared Key
- 💬 Friendly and intuitive chat UI for the command-line interface
- 🔄 Command history support

## 🚀 Usage

### Running with Docker

```bash
# Default (A2A) mode
docker run -it ghcr.io/cnoe-io/agent-chat-cli:stable

# A2A mode (host-network may be required if your agent runs on the host)
docker run -it --network=host \
  -e AGENT_CHAT_PROTOCOL=a2a \
  -e A2A_HOST=localhost -e A2A_PORT=8000 \
  ghcr.io/cnoe-io/agent-chat-cli:stable

# SLIM mode
docker run -it \
  -e AGENT_CHAT_PROTOCOL=slim \
  -e SLIM_ENDPOINT=127.0.0.1:46357 \
  -e SLIM_REMOTE_CARD=http://127.0.0.1:46357/.well-known/agent.json \
  ghcr.io/cnoe-io/agent-chat-cli:stable
```

### Running with UVX

```bash
# Use env var to choose protocol (defaults to slim when omitted)
AGENT_CHAT_PROTOCOL=a2a uvx https://github.com/cnoe-io/agent-chat-cli.git
AGENT_CHAT_PROTOCOL=slim uvx https://github.com/cnoe-io/agent-chat-cli.git

# Or explicitly specify the subcommand
uvx https://github.com/cnoe-io/agent-chat-cli.git a2a
uvx https://github.com/cnoe-io/agent-chat-cli.git slim
```

## Selecting the protocol via environment variable

The CLI and Docker image can choose the protocol at runtime using:

- **AGENT_CHAT_PROTOCOL**: one of `a2a` or `slim` (default: `a2a`)
- **AGENT_CHAT_DEBUG**: set to `1` to enable debug logging in the container/CLI

Examples:

- Local: `AGENT_CHAT_PROTOCOL=a2a uv run python -m agent_chat_cli`
- Docker: `docker run -e AGENT_CHAT_PROTOCOL=slim ghcr.io/cnoe-io/agent-chat-cli:stable`

Protocol-specific configuration:

- **A2A**
  - `A2A_HOST` (default: `localhost`)
  - `A2A_PORT` (default: `8000`)
  - `A2A_TOKEN` (optional)
  - `A2A_TLS` (optional; `true`/`1`/`yes` to enable TLS)
- **SLIM**
  - `SLIM_ENDPOINT` (e.g., `127.0.0.1:46357`)
  - `SLIM_REMOTE_CARD` (URL, JSON string, or file path; e.g., `http://127.0.0.1:46357/.well-known/agent.json`)

## ⚙️ [Optional] UVX Setup

### Create/Update `.env` (or input interactively)

```env
## A2A Agent Configuration
A2A_HOST=localhost
A2A_PORT=8000
A2A_TOKEN=

## MCP Server Configuration
MCP_HOST=localhost
MCP_PORT=9000

## SLIM Agent Configuration
SLIM_ENDPOINT=127.0.0.1:46357
SLIM_REMOTE_CARD=http://127.0.0.1:46357/.well-known/agent.json
```

### Running locally

```bash
make run-a2a-client
make run-slim-client
AGENT_CHAT_PROTOCOL=a2a uv run python -m agent_chat_cli
AGENT_CHAT_PROTOCOL=slim uv run python -m agent_chat_cli
```

### SLIM CLI Examples

```bash
uv run python -m agent_chat_cli slim -e 127.0.0.1:46357 -c http://127.0.0.1:46357/.well-known/agent.json
uvx https://github.com/cnoe-io/agent-chat-cli.git slim
```

## Quick Demos

### Google A2A Demo

![a2a_docker_terminal_demo](https://github.com/user-attachments/assets/2a84fd6b-102f-425b-8312-501b47c11e81)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
