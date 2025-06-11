FROM python:3.13-slim

WORKDIR /app

# Install Poetry and uv first, so this layer can be cached
RUN pip install --no-cache-dir poetry uv && \
  poetry config virtualenvs.create false

# Copy only dependency files first to leverage Docker cache
COPY pyproject.toml poetry.lock* README.md /app/

# Install dependencies (no source code yet)
RUN poetry install --no-interaction --no-ansi --no-root

# Now copy the rest of the source code
COPY . /app

ENTRYPOINT ["uv", "run", "python", "-m", "agent_chat_cli", "a2a"]