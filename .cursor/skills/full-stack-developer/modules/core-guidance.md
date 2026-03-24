# Full Stack Developer Core Guidance

## Modern Fullstack Development Principles

### **1. Technology Stack Selection Matrix**

#### **Frontend Frameworks (2026)**
```typescript
// Primary Choices
React 18+ (TypeScript)     // Most popular, ecosystem, performance
Vue 3+ (TypeScript)        // Simpler learning curve, excellent DX
Angular 17+ (TypeScript)   // Enterprise-grade, comprehensive
Svelte 4+ (TypeScript)     // Compile-time optimization, fast runtime
SolidJS (TypeScript)       // Reactive, fine-grained updates

// UI Libraries
Chakra UI                  // Accessible, themeable, comprehensive
Material-UI (MUI)          // Google Material Design
Tailwind CSS               // Utility-first, highly customizable
Ant Design                 // Enterprise components
Radix UI                   // Unstyled, accessible primitives
```

#### **Backend Frameworks**
```python
# Python (Recommended for AI/ML integration)
FastAPI (ASGI)            // Async, auto-docs, type validation
Django 5.0+               // Batteries included, rapid development
Flask (with extensions)    // Lightweight, flexible
Starlette                  // Async micro-framework

# Node.js
Express.js                // Mature, middleware ecosystem
NestJS (TypeScript)       // Enterprise, dependency injection
Fastify                   // Performance-focused
Koa.js                    // Async/await native

# Other Languages
Go (Gin/Echo)             // High performance, concurrency
Rust (Axum)               // Memory safety, performance
```

#### **Database Selection**
```sql
-- Relational (ACID, complex queries)
PostgreSQL 15+           -- Advanced features, JSON support
MySQL 8.0+               -- Performance, ecosystem
SQLite                   -- Embedded, serverless

-- NoSQL (Scalability, flexibility)
MongoDB 7+               -- Document-oriented
Redis 7+                 -- In-memory, caching, pub/sub
ChromaDB                 -- Vector database for AI/RAG
```

### **2. Architecture Patterns**

#### **Application Architecture Decision Tree**
```
Single Page Application (SPA)?
├── Yes → Choose: React/Vue/Angular/Svelte
│   ├── API Integration → REST/GraphQL/WebSocket
│   ├── State Management → Zustand/Redux/Pinia/Vuex
│   └── Routing → React Router/Vue Router/Angular Router
└── No → Server-Side Rendering (SSR)?
    ├── Yes → Choose: Next.js/Nuxt.js/Angular Universal
    │   ├── Static Generation → Next.js ISR/Nuxt.js SSG
    │   └── Hybrid Approach → Combine SSR + SPA
    └── No → Traditional MPA with HTMX/Alpine.js
```

#### **API Architecture Patterns**
```typescript
// REST API Design
interface RESTEndpoints {
  // Resource-based URLs
  GET    /api/users         // List users
  POST   /api/users         // Create user
  GET    /api/users/:id     // Get specific user
  PUT    /api/users/:id     // Update user (full)
  PATCH  /api/users/:id     // Update user (partial)
  DELETE /api/users/:id     // Delete user
}

// GraphQL Schema Design
type Query {
  users(first: Int, after: String): UserConnection!
  user(id: ID!): User
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
}
```

### **3. Development Workflow Excellence**

#### **Modern Development Environment**
```json
// .vscode/settings.json or .cursor/settings.json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "emmet.includeLanguages": {
    "typescript": "html",
    "typescriptreact": "html"
  },
  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"]
  ]
}
```

#### **Git Workflow for Fullstack Teams**
```bash
# Branch naming convention
feature/user-authentication
bugfix/login-validation
hotfix/security-patch
refactor/api-optimization
docs/setup-instructions

# Commit message format
type(scope): description

# Types: feat, fix, docs, style, refactor, test, chore
feat(auth): add JWT token refresh
fix(api): handle null user data
docs(readme): update setup instructions
```

#### **Code Quality Gates**
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20]
        python-version: [3.10, 3.11]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          npm ci
          pip install -r requirements.txt

      - name: Lint
        run: |
          npm run lint
          ruff check . --fix

      - name: Type check
        run: |
          npm run type-check
          mypy .

      - name: Test
        run: |
          npm test -- --coverage
          pytest --cov=. --cov-report=xml

      - name: Build
        run: npm run build
```

### **4. Security-First Development**

#### **Authentication Architecture**
```typescript
// JWT Token Management
interface AuthTokens {
  accessToken: string;   // Short-lived (15 min)
  refreshToken: string;  // Long-lived (7 days)
  tokenType: 'Bearer';
}

class AuthManager {
  private tokens: AuthTokens | null = null;

  async login(credentials: LoginCredentials): Promise<void> {
    const response = await api.post('/auth/login', credentials);
    this.tokens = response.data;
    this.setupTokenRefresh();
  }

  private setupTokenRefresh(): void {
    // Refresh token 5 minutes before expiry
    const refreshTime = this.getTokenExpiry() - 5 * 60 * 1000;
    setTimeout(() => this.refreshToken(), refreshTime);
  }

  private async refreshToken(): Promise<void> {
    try {
      const response = await api.post('/auth/refresh', {
        refreshToken: this.tokens!.refreshToken
      });
      this.tokens!.accessToken = response.data.accessToken;
      this.setupTokenRefresh();
    } catch (error) {
      this.logout();
    }
  }
}
```

#### **Input Validation & Sanitization**
```python
# FastAPI with Pydantic validation
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
import bleach

app = FastAPI()

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8)
    bio: str | None = Field(None, max_length=500)

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric with _ and - allowed')
        return v

    @validator('bio')
    def sanitize_bio(cls, v):
        if v:
            # Remove potentially dangerous HTML
            return bleach.clean(v, tags=['p', 'br', 'strong', 'em'], strip=True)
        return v

@app.post('/users/')
async def create_user(user: UserCreate):
    # Password hashing happens here
    hashed_password = hash_password(user.password)

    # Create user in database
    db_user = await create_user_in_db(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        bio=user.bio
    )

    return {"id": db_user.id, "username": db_user.username}
```

### **5. Performance Optimization Strategies**

#### **Frontend Performance**
```typescript
// Lazy loading with React
import { Suspense, lazy } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));
const AnalyticsDashboard = lazy(() => import('./AnalyticsDashboard'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/heavy" element={<HeavyComponent />} />
        <Route path="/analytics" element={<AnalyticsDashboard />} />
      </Routes>
    </Suspense>
  );
}

// Image optimization with Next.js
import Image from 'next/image';

export default function OptimizedImage({ src, alt, width, height }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={width}
      height={height}
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
      priority={false} // Only true for above-the-fold images
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  );
}
```

#### **Backend Performance**
```python
# Async database operations with SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

# pragma: allowlist secret
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/db",
    pool_size=10,         # Connection pool size
    max_overflow=20,      # Max additional connections
    pool_recycle=3600,   # Recycle connections after 1 hour
)

async def get_user_with_posts(user_id: int) -> User:
    async with AsyncSession(engine) as session:
        # Eager loading to prevent N+1 queries
        result = await session.execute(
            select(User)
            .options(selectinload(User.posts))
            .where(User.id == user_id)
        )
        return result.scalar_one()
```

#### **Caching Architecture**
```python
# Multi-level caching strategy
from cachetools import TTLCache
from redis.asyncio import Redis
import asyncio

class CacheManager:
    def __init__(self):
        # L1: In-memory cache (fastest, limited size)
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)

        # L2: Redis cache (distributed, persistent)
        self.redis_cache = Redis(host='localhost', port=6379)

        # L3: Database cache (slowest, most persistent)
        self.db_cache = DatabaseCache()

    async def get(self, key: str) -> Any:
        # Check L1 cache first
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Check L2 cache
        redis_value = await self.redis_cache.get(key)
        if redis_value:
            # Promote to L1 cache
            self.memory_cache[key] = redis_value
            return redis_value

        # Check L3 cache
        db_value = await self.db_cache.get(key)
        if db_value:
            # Promote to higher caches
            self.memory_cache[key] = db_value
            await self.redis_cache.set(key, db_value, ex=3600)
            return db_value

        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        # Set all levels
        self.memory_cache[key] = value
        await self.redis_cache.set(key, value, ex=ttl)
        await self.db_cache.set(key, value, ttl)
```

### **6. Testing Strategy**

#### **Testing Pyramid Implementation**
```typescript
// Unit Tests (50% of tests)
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('validates email format', async () => {
    render(<LoginForm onSubmit={jest.fn()} />);

    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    await userEvent.type(emailInput, 'invalid-email');
    await userEvent.click(submitButton);

    expect(screen.getByText('Please enter a valid email')).toBeInTheDocument();
  });

  it('calls onSubmit with form data', async () => {
    const mockSubmit = jest.fn();
    render(<LoginForm onSubmit={mockSubmit} />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    await userEvent.type(emailInput, 'user@example.com');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(submitButton);

# pragma: allowlist secret
    expect(mockSubmit).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password123'
    });
  });
});
```

```python
# Integration Tests (30% of tests)
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    # Create tables
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=engine)

def test_create_and_retrieve_user(setup_database):
    # Create user
    response = client.post(
        "/users/",
        json={
# pragma: allowlist secret
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 201
    user_data = response.json()

    # Retrieve user
    response = client.get(f"/users/{user_data['id']}")
    assert response.status_code == 200
    retrieved_user = response.json()

    assert retrieved_user["username"] == "testuser"
    assert retrieved_user["email"] == "test@example.com"
```

#### **End-to-End Tests (20% of tests)**
```typescript
// E2E tests with Playwright
import { test, expect } from '@playwright/test';

test.describe('User Registration Flow', () => {
  test('should allow user to register and login', async ({ page }) => {
    // Navigate to registration page
    await page.goto('/register');

    // Fill registration form
    await page.fill('[data-testid="username"]', 'testuser');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.fill('[data-testid="confirm-password"]', 'password123');

    // Submit form
    await page.click('[data-testid="register-button"]');

    // Should redirect to login page
    await expect(page).toHaveURL('/login');

    // Login with new credentials
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome-message"]')).toContainText('Welcome, testuser');
  });
});
```

### **7. Deployment & DevOps Excellence**

#### **Container Orchestration**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    image: myapp-frontend:${TAG}
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_URL=https://api.myapp.com
    depends_on:
      - api
    restart: unless-stopped

  api:
    image: myapp-api:${TAG}
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

#### **Infrastructure as Code**
```hcl
# Terraform configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1d0"  # Ubuntu 22.04 LTS
  instance_type = "t3.micro"

  tags = {
    Name = "WebServer"
  }
}

resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine              = "postgres"
  engine_version      = "15.0"
  instance_class      = "db.t3.micro"
  db_name             = var.db_name
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = true
}
```

### **8. Monitoring & Observability**

#### **Application Monitoring Setup**
```python
# Prometheus metrics in FastAPI
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest
import time

app = FastAPI()

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)

    return response

@app.get('/metrics')
async def metrics():
    return Response(generate_latest(), media_type='text/plain')
```

#### **Logging Configuration**
```python
# Structured logging setup
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

# Configure logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = CustomJsonFormatter(
    '%(timestamp)s %(level)s %(module)s %(function)s %(line)s %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info('User login successful', extra={
    'user_id': user.id,
    'ip_address': request.client.host,
    'user_agent': request.headers.get('user-agent')
})
```

### **9. SOTA Builder Integration Patterns**

#### **Post-Generation Customization**
```powershell
# Generate base application
.\new-fullstack-app.ps1 -AppName "MyCustomApp" -IncludeAI -IncludeMCP

# Customize generated code
cd MyCustomApp

# Add custom AI provider
# backend/app/services/ai_service.py
class CustomAIProvider:
    async def generate_response(self, prompt: str) -> str:
        # Custom AI logic here
        return await self.custom_model.generate(prompt)

# Add custom MCP tools
# backend/mcp_server.py
@mcp.tool()
async def custom_business_logic(param: str) -> dict:
    """Custom business logic tool."""
    result = await process_custom_logic(param)
    return {"result": result, "processed_at": datetime.now().isoformat()}
```

#### **Builder Workflow Integration**
```yaml
# Custom CI/CD with builder integration
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  generate:
    runs-on: windows-latest  # Builder requires PowerShell
    steps:
      - uses: actions/checkout@v4

      - name: Generate App with Builder
        run: |
          .\scripts\new-fullstack-app.ps1 `
            -AppName "GeneratedApp" `
            -IncludeAI `
            -IncludeMCP `
            -IncludeMonitoring

      - name: Customize Generated App
        run: |
          # Apply custom templates
          Copy-Item -Path "templates/*" -Destination "GeneratedApp/" -Recurse -Force

      - name: Build Docker Images
        working-directory: GeneratedApp
        run: docker-compose build

      - name: Run Tests
        working-directory: GeneratedApp
        run: docker-compose run --rm api pytest

      - name: Deploy
        run: |
          # Deploy logic here
```

---

**This core guidance provides the foundation for modern fullstack development, with the SOTA Fullstack App Builder serving as the ultimate automation tool for rapid application development.**
