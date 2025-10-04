## Unreleased

### Feat

- improve A2A streaming response handling and add comprehensive tests
- enhance A2A streaming response handling with improved artifact processing

### Fix

- update pyproject
- lint
- **merge**: merge with main
- update README.md
- update README.md

## 0.2.7 (2025-09-18)

### Feat

- add OAuth Bearer token authentication support
- **streaming**: implement streaming for a2a client
- **slim**: initial slim implementation

### Fix

- **lint**: ruff check
- **slim**: fail client if agent card is unavailable
- **lint**: ruff check
- **slim**: conditionally run slim based on env var and fix topic logic
- **slim**: use default topic
- **a2a-sdk**: pin a2a-sdk==0.2.16 to avoid breaking change in 0.3.0
- **a2a-sdk**: pin a2a-sdk==0.2.16 to avoid breaking change in 0.3.0

## 0.2.5 (2025-07-11)

### Fix

- **Dockerfile**: use poetry --quiet

## 0.2.4 (2025-07-11)

### Fix

- **Dockerfile**: simplify docker run

## 0.2.3 (2025-06-18)

### Fix

- client always uses 0.0.0.0

## 0.2.2 (2025-06-18)

### Fix

- **pyproject.toml**: restore project.scripts
- uv.lock

## 0.2.1 (2025-06-18)

### Feat

- add cz and update changelog

### Fix

- commitzen
- commitzen
- commitzen
- commitzen
- commitzen
- **poetry**: pyproject.toml to be commitizen compatible

## 0.2.0 (2025-06-18)

### Feat

- add support for tls endpoints

### Fix

- pyproject.toml version
- ruff lint
- **clean-up**: remove get_available_tools

## 0.0.4 (2025-06-17)

### Fix

- **httpx**: set to 300 second timeout for long agent operations
- **httpx**: set to 300 second timeout for long agent operations

## 0.0.2 (2025-06-10)

### Fix

- use A2A_HOST and A2A_PORT

## 0.0.1 (2025-06-10)

### Feat

- add github actions to publish containers
- read A2A agent card from CLI
- add package executable
- add package executable

### Fix

- **README**: update docker command
- **README.md**: updates and tags
- updates
- updates and reconcile from main
- updated message_id
- update context_id
- **httpx**: bump timeout to 120 seconds for longer requests
- suppress extra logging by a2a client
- update exception with EOFError
- **a2**: event loop
- update history and readme file
- update python package agent-chat-cli
- **MAINTAINERS.md**: updates
- **README.md**: add demos
