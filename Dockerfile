FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ADD . /app

WORKDIR /app

RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "server/main.py"]