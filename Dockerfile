FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ADD . /app

WORKDIR /app

RUN uv sync

EXPOSE 8000

ARG API_KEY_MISTRAL

ENV MISTRAL_API_KEY=$mistral_api_key

CMD ["uv", "run", "fastapi", "run", "server/main.py"]