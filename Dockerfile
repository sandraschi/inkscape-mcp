# inkscape-mcp HTTP MCP server (Inkscape CLI batch in container).
#
# Build:
#   docker build --target production -t ghcr.io/sandraschi/inkscape-mcp:local .
#
# Run:
#   docker run --rm -p 10900:10900 -p 9074:9074 ghcr.io/sandraschi/inkscape-mcp:local
#
# Hands-In (GUI watch) requires Inkscape GUI on the HOST; container is Hands-Off batch.

FROM python:3.12-slim AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl inkscape \
    && rm -rf /var/lib/apt/lists/*

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=10900
ENV MCP_TRANSPORT=http
ENV PROMETHEUS_PORT=9074
ENV INKSCAPE_MCP_METRICS_ENABLED=true
ENV INKSCAPE_MCP_LOG_FORMAT=json
ENV INKSCAPE_MCP_LOG_LEVEL=INFO

WORKDIR /app

FROM base AS production

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir -e ".[monitoring,http]"

RUN useradd --create-home --shell /bin/bash mcp \
    && mkdir -p /app/logs \
    && chown -R mcp:mcp /app

USER mcp

EXPOSE 10900 9074

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:10900/api/health', timeout=5)"

CMD ["python", "-m", "inkscape_mcp.main", "--mode", "http", "--host", "0.0.0.0", "--port", "10900"]

ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="Inkscape MCP" \
      org.opencontainers.image.description="Agentic Inkscape MCP server (batch CLI + fleet HTTP)" \
      org.opencontainers.image.vendor="FlowEngineer sandraschi" \
      org.opencontainers.image.source="https://github.com/sandraschi/inkscape-mcp" \
      org.opencontainers.image.licenses="MIT"
