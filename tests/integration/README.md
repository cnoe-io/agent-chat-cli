# Integration Tests

This directory contains integration tests that require live agents running on `localhost:8000` (or other configured endpoints).

## Purpose

These tests are **diagnostic/debugging scripts** that:
- Test real streaming behavior with actual network calls
- Verify end-to-end functionality with live agents
- Help diagnose issues with streaming, partial results, and UI rendering
- Are meant to be run manually during development/debugging

## Running Integration Tests

To run all integration tests:
```bash
make test-integration
```

To run a specific integration test:
```bash
uv run python tests/integration/test_partial_result.py
```

## Prerequisites

- A live agent must be running (usually at `http://localhost:8000`)
- For docker-compose deployments, ensure agents are started:
  ```bash
  cd /path/to/ai-platform-engineering
  docker-compose -f docker-compose.dev.yaml --profile=p2p-no-rag up -d
  ```

## Note

These tests are **excluded from `make test`** because they:
- Require external dependencies (live agents)
- Are slow (network calls, streaming)
- Are meant for manual debugging, not CI/CD

Use `make test` for fast unit tests, and `make test-integration` when you need to verify behavior with real agents.

