# Welcome to the A2A/MCP Multi-Protocol Agentic Chat Client 🤖💬

Effortlessly interact with multiple protocols using a lightweight, intuitive command-line chat interface. Whether you're managing A2A or MCP agents, this tool has you covered!

[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

[![Docker Build and Push](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/docker-build-publish.yml/badge.svg)](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/docker-build-publish.yml) [![Ruff Linter](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/lint.yml/badge.svg)](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/lint.yml) [![Conventional Commits](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/conventional_commits.yml/badge.svg)](https://github.com/cnoe-io/agent-chat-cli/actions/workflows/conventional_commits.yml)

## ✨ Features

- 🔌 Easy integration with multiple protocols (A2A, MCP)
- 💬 Friendly and intuitive chat UI for the command-line interface
- 🚀 Lightweight and fast
- 🔄 Command history support

## 🚀 Usage

### Running with Docker

```bash
# Use --network=host to connect to A2A agent on host network
docker run -it --network=host ghcr.io/cnoe-io/agent-chat-cli:stable
```

### Running with UVX

```bash
uvx https://github.com/cnoe-io/agent-chat-cli.git <a2a|mcp>
```

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
```

### Running locally

```bash
make run-a2a-client
```

## Quick Demos

### Google A2A Demo

![a2a_docker_terminal_demo](https://github.com/user-attachments/assets/2a84fd6b-102f-425b-8312-501b47c11e81)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
