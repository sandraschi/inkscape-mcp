# Multi-stage build for Inkscape MCP Server
FROM python:3.12-slim as base

# Metadata
LABEL maintainer="Sandra Schipal <sandra@sandraschi.dev>"
LABEL description="FastMCP server for professional vector graphics using Inkscape"
LABEL version="1.2.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Inkscape dependencies
    inkscape \
    # Image processing libraries
    libjpeg62-turbo-dev \
    libpng-dev \
    libtiff5-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    # System utilities
    curl \
    git \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r inkscape && useradd -r -g inkscape inkscape

# Set work directory
WORKDIR /app

# Copy and install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install -e .

# Copy source code
COPY src/ ./src/

# Change ownership to non-root user
RUN chown -R inkscape:inkscape /app
USER inkscape

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import inkscape_mcp; print('Health check passed')" || exit 1

# Default command
CMD ["inkscape-mcp", "--help"]

# --- Development stage ---
FROM base as development

# Switch back to root for development
USER root

# Install development dependencies
RUN pip install -e ".[dev]"

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to non-root user
USER inkscape

# Development command
CMD ["sleep", "infinity"]

# --- Production stage ---
FROM base as production

# Add version info
ARG VERSION=1.2.0
ENV INKSCAPE_MCP_VERSION=${VERSION}

# Expose port if HTTP server is used
EXPOSE 8000

# Production command with proper signal handling
CMD ["python", "-m", "inkscape_mcp.main"]