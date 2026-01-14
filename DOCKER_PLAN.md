# Dockerization Plan for Inkscape MCP Server

## Overview
This document outlines the comprehensive plan for containerizing the Inkscape MCP Server to enable consistent deployment, testing, and distribution across different environments.

## Current Status
- ✅ **Headless Mode Ready**: Server already uses `--batch-process` for GUI-less operation
- ✅ **Cross-Platform Detection**: Multi-platform Inkscape detection implemented
- ✅ **CLI Wrapper**: Robust subprocess handling with timeout and error management
- ✅ **Testing Scaffold**: Comprehensive test suite with fixtures and mocks

## Phase 1: Core Containerization (Week 1)

### 1.1 Base Image Selection
**Options:**
- `ubuntu:22.04` - Full Ubuntu with package management
- `debian:bookworm-slim` - Minimal Debian for smaller size
- `fedora:latest` - Alternative with different package ecosystem

**Recommendation:** `ubuntu:22.04` for maximum compatibility

### 1.2 Multi-Stage Dockerfile Strategy
```dockerfile
# Build stage
FROM ubuntu:22.04 AS builder
# Install build dependencies and compile if needed

# Runtime stage
FROM ubuntu:22.04 AS runtime
# Copy built artifacts and runtime dependencies
```

### 1.3 Inkscape Installation Strategies

#### Option A: System Package (Recommended)
```dockerfile
RUN apt-get update && apt-get install -y \
    inkscape \
    python3 python3-pip \
    # Additional dependencies
    && rm -rf /var/lib/apt/lists/*
```

**Pros:**
- Official Ubuntu packages
- Automatic security updates
- Smaller image size (~500MB)

**Cons:**
- Version may lag behind latest
- Limited to Ubuntu package versions

#### Option B: Snap Package
```dockerfile
RUN apt-get install -y snapd \
    && snap install inkscape
```

**Pros:**
- Latest Inkscape versions
- Automatic updates

**Cons:**
- Larger image size
- Snap complexity in containers
- Permission issues

#### Option C: Compile from Source
```dockerfile
RUN apt-get install -y build-essential \
    && wget https://inkscape.org/gallery/item/37362/inkscape-1.3.tar.xz \
    && # Compilation steps...
```

**Pros:**
- Latest features and bug fixes
- Customizable build

**Cons:**
- Complex build process
- Large build time
- Maintenance overhead

### 1.4 Python Environment
```dockerfile
# Use system Python to avoid conflicts
RUN pip install --no-cache-dir -r requirements.txt

# Or use virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt
```

### 1.5 Security Considerations
- **Non-root user**: Run as non-privileged user
- **Minimal attack surface**: Remove unnecessary packages
- **No hardcoded secrets**: Use environment variables
- **Read-only filesystem**: Use read-only root filesystem where possible

## Phase 2: Advanced Features (Week 2-3)

### 2.1 GPU Acceleration Support
```dockerfile
# For GPU-enabled containers
FROM nvidia/cuda:11.8-runtime-ubuntu22.04

# Install CUDA-enabled Inkscape build
RUN apt-get install -y nvidia-cuda-toolkit \
    && # Custom Inkscape build with GPU support
```

### 2.2 Multi-Architecture Support
```dockerfile
# Use buildx for multi-platform builds
FROM --platform=$BUILDPLATFORM ubuntu:22.04

# Architecture-specific installations
RUN case "$TARGETPLATFORM" in \
    "linux/amd64") echo "x86_64 build" ;; \
    "linux/arm64") echo "ARM64 build" ;; \
    *) echo "Unknown architecture" ;; \
    esac
```

### 2.3 Layer Caching Optimization
```dockerfile
# Order for optimal caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ .
RUN pip install --no-cache-dir -e .
```

## Phase 3: CI/CD Integration (Week 4)

### 3.1 GitHub Actions Workflow
```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Build Docker image
      run: docker build -t inkscape-mcp .
    - name: Test container
      run: docker run --rm inkscape-mcp --help
```

### 3.2 Automated Testing in Containers
```yaml
- name: Run tests in container
  run: |
    docker run --rm \
      -v $(pwd):/workspace \
      -w /workspace \
      inkscape-mcp \
      python -m pytest tests/
```

### 3.3 Multi-Platform Builds
```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build multi-platform image
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ghcr.io/your-org/inkscape-mcp:latest
```

## Phase 4: Distribution and Deployment (Week 5-6)

### 4.1 Registry Strategy
- **GitHub Container Registry**: `ghcr.io/your-org/inkscape-mcp`
- **Docker Hub**: `your-org/inkscape-mcp`
- **Self-hosted**: For enterprise deployments

### 4.2 Version Tagging Strategy
```bash
# Semantic versioning
docker tag inkscape-mcp:latest inkscape-mcp:v1.1.0
docker tag inkscape-mcp:latest inkscape-mcp:v1.1

# Git-based versioning
docker tag inkscape-mcp:latest inkscape-mcp:git-${GITHUB_SHA::8}
```

### 4.3 Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inkscape-mcp
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: inkscape-mcp
        image: ghcr.io/your-org/inkscape-mcp:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### 4.4 Docker Compose for Development
```yaml
version: '3.8'
services:
  inkscape-mcp:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - INKSCAPE_EXECUTABLE=/usr/bin/inkscape
    restart: unless-stopped
```

## Phase 5: Monitoring and Observability (Week 7-8)

### 5.1 Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.path.insert(0, 'src'); import inkscape_mcp; print('OK')"
```

### 5.2 Logging Configuration
```dockerfile
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Mount log volume
VOLUME ["/app/logs"]
```

### 5.3 Metrics Collection
```python
# Add Prometheus metrics endpoint
from prometheus_client import start_http_server, Counter, Histogram

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')
```

## Implementation Timeline

### Week 1: Core Containerization
- [ ] Create basic Dockerfile
- [ ] Test Inkscape installation in container
- [ ] Verify MCP server runs in container
- [ ] Basic CI pipeline

### Week 2: Advanced Features
- [ ] Multi-stage builds
- [ ] GPU support investigation
- [ ] Performance optimization
- [ ] Security hardening

### Week 3: CI/CD Pipeline
- [ ] GitHub Actions workflows
- [ ] Automated testing in containers
- [ ] Multi-platform builds
- [ ] Registry integration

### Week 4: Distribution
- [ ] Version tagging strategy
- [ ] Docker Compose setup
- [ ] Documentation updates
- [ ] Registry publishing

### Week 5: Production Ready
- [ ] Kubernetes manifests
- [ ] Monitoring setup
- [ ] Backup strategies
- [ ] Rollback procedures

### Week 6: Optimization & Polish
- [ ] Performance benchmarking
- [ ] Size optimization
- [ ] Documentation completion
- [ ] User acceptance testing

## Success Metrics

### Technical Metrics
- **Image Size**: < 800MB (target: < 600MB)
- **Startup Time**: < 30 seconds
- **Memory Usage**: < 100MB idle, < 500MB active
- **Test Coverage**: > 85%
- **Build Time**: < 10 minutes

### Operational Metrics
- **Deployment Success Rate**: > 99%
- **Container Uptime**: > 99.9%
- **Error Rate**: < 1%
- **Response Time**: < 5 seconds average

## Risk Mitigation

### Technical Risks
1. **Inkscape GUI Dependencies**: Already mitigated by headless mode
2. **X11 Requirements**: Using `--batch-process` eliminates GUI dependencies
3. **Performance Degradation**: Will benchmark and optimize
4. **Security Vulnerabilities**: Regular base image updates and scanning

### Operational Risks
1. **Registry Availability**: Multi-registry strategy (GHCR + Docker Hub)
2. **Build Failures**: Comprehensive CI testing before deployment
3. **Resource Limits**: Proper resource requests and limits in K8s
4. **Update Management**: Automated update pipelines

## Alternative Approaches

### 1. Podman Instead of Docker
- **Pros**: Daemonless, better security, rootless containers
- **Cons**: Less ecosystem support, learning curve

### 2. Distroless Images
- **Pros**: Minimal attack surface, smaller images
- **Cons**: Complex Python application packaging

### 3. Apptainer/Singularity
- **Pros**: HPC-friendly, no root required
- **Cons**: Limited ecosystem, learning curve

## Conclusion

Dockerizing the Inkscape MCP Server is **highly feasible** due to the existing headless architecture. The 8-week plan provides a comprehensive approach to production-ready containerization with proper testing, security, and operational considerations.

**Priority**: Low for initial development, but **essential** for production deployment, CI/CD, and multi-platform distribution.