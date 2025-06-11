FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* README.md /app/

RUN pip install --no-cache-dir poetry uv && \
  poetry config virtualenvs.create false

COPY . /app

RUN poetry install --no-interaction --no-ansi --no-root

ENTRYPOINT ["uv", "run", "python", "-m", "agent_chat_cli", "a2a"]