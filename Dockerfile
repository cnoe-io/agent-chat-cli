FROM python:3.13-slim

WORKDIR /app

# Install Poetry and uv first, so this layer can be cached
RUN pip install --no-cache-dir poetry

RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false
RUN poetry config cache-dir /app/.cache

# Now copy the rest of the source code
COPY . /app

# Install dependencies (no source code yet)
RUN poetry install --no-interaction --no-root

ENTRYPOINT ["poetry", "--quiet", "run", "python", "-m", "agent_chat_cli", "a2a"]