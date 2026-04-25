# Technology Stack Selection

## User Management Portal — Complete Technology Stack

---

## 1. Technology Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TECHNOLOGY STACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        FRONTEND LAYER                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │  React 18   │  │ TypeScript  │  │ Tailwind CSS│  │ Vite       │ │   │
│  │  │  (UI Lib)   │  │  (Typing)   │  │  (Styling)  │  │ (Build)    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ React Router│  │ React Query │  │ Zustand     │  │ Axios      │ │   │
│  │  │  (Routing)  │  │  (Server State)│ (Client State)│  │ (HTTP)     │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼ HTTPS/JSON                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        BACKEND LAYER                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │  FastAPI    │  │ Python 3.11 │  │ SQLAlchemy  │  │ Alembic    │ │   │
│  │  │  (Web API)  │  │  (Language) │  │  (ORM)      │  │ (Migrations)│ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ Pydantic v2 │  │ AsyncPG     │  │ Passlib     │  │ PyJWT      │ │   │
│  │  │ (Validation)│  │  (DB Driver)│  │ (Passwords) │  │ (Tokens)   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼ SQL/TCP                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        DATA LAYER                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ PostgreSQL  │  │ Redis       │  │ Azure Blob  │  │ (Optional) │ │   │
│  │  │    15       │  │ (Sessions)  │  │  (Files)    │  │            │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    INFRASTRUCTURE LAYER                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ Azure App   │  │ Docker      │  │ GitHub      │  │ Azure      │ │   │
│  │  │   Service   │  │ (Container) │  │  Actions    │  │ Monitor    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Stack

### 2.1 Core Framework: React 18

**Version**: 18.2.0  
**License**: MIT

```typescript
// Key React 18 features utilized
import { Suspense, lazy, useTransition } from 'react';

// Concurrent features for better UX
const UserDashboard = lazy(() => import('./pages/UserDashboard'));

function App() {
  const [isPending, startTransition] = useTransition();
  
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <UserDashboard />
    </Suspense>
  );
}
```

**Justification**:
| Factor | React 18 | Vue 3 | Angular 17 |
|--------|----------|-------|------------|
| Bundle Size | 40kb | 34kb | 150kb+ |
| TypeScript Support | Excellent | Good | Excellent |
| Learning Curve | Medium | Low | High |
| Ecosystem | Largest | Large | Enterprise |
| Concurrent Features | ✅ Yes | ⚠️ Limited | ✅ Yes |
| Team Familiarity | High | Medium | Low |
| **Decision** | **✅ Selected** | ❌ | ❌ |

### 2.2 Language: TypeScript 5.3

```typescript
// Strict type checking configuration
tsconfig.json:
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### 2.3 Styling: Tailwind CSS 3.4

```javascript
// tailwind.config.js
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    }
  },
  plugins: [require('@tailwindcss/forms')],
}
```

**Justification**:
- Utility-first approach reduces CSS bundle size
- JIT compiler generates only used styles
- Built-in responsive design utilities
- Excellent developer experience with IntelliSense

### 2.4 State Management

#### Server State: React Query (TanStack Query) v5
```typescript
import { useQuery, useMutation, QueryClient } from '@tanstack/react-query';

// Query client configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    }
  }
});

// User list query
function useUsers(params: UserListParams) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => api.getUsers(params),
  });
}

// User mutation
function useUpdateUser() {
  return useMutation({
    mutationFn: api.updateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    }
  });
}
```

#### Client State: Zustand
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' }
  )
);
```

### 2.5 Routing: React Router v6

```typescript
import { createBrowserRouter, RouterProvider, redirect } from 'react-router-dom';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      {
        path: 'login',
        element: <LoginPage />,
        loader: () => {
          if (isAuthenticated()) return redirect('/dashboard');
          return null;
        }
      },
      {
        path: 'signup',
        element: <SignupPage />,
      },
      {
        path: 'dashboard',
        element: <ProtectedRoute><Dashboard /></ProtectedRoute>,
        loader: usersLoader,
      },
      {
        path: 'users/:id/edit',
        element: <ProtectedRoute><EditUserPage /></ProtectedRoute>,
        loader: userLoader,
      }
    ]
  }
]);
```

---

## 3. Backend Stack

### 3.1 Framework: FastAPI 0.109

```python
# main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import auth, users
from app.core.config import settings
from app.db.session import engine
from app.models.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        pass
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="User Management Portal API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
```

**Justification**:
| Factor | FastAPI | Django | Flask | Express.js |
|--------|---------|--------|-------|------------|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Type Safety | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Async Support | Native | Limited | Extension | Native |
| Auto Documentation | ✅ Built-in | ❌ | ❌ | ⚠️ Swagger |
| Learning Curve | Medium | High | Low | Low |
| **Decision** | **✅ Selected** | ❌ | ❌ | ❌ |

### 3.2 Database: PostgreSQL 15

```sql
-- Key features utilized
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- JSONB for flexible metadata
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Full-text search
CREATE INDEX idx_users_search ON users 
USING gin(to_tsvector('english', full_name || ' ' || email));
```

**Justification**:
- ACID compliance for data integrity
- JSONB support for flexible schemas
- Row-level security for multi-tenant scenarios
- Excellent Python ecosystem support
- Azure managed service available

### 3.3 ORM: SQLAlchemy 2.0 (Async)

```python
# models/user.py
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from uuid import uuid4

from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
```

### 3.4 Migrations: Alembic

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.db.base_class import Base
from app.models import user, audit_log  # Import all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
```

---

## 4. Infrastructure Stack

### 4.1 Cloud Provider: Microsoft Azure

| Service | Purpose | Tier |
|---------|---------|------|
| App Service | Host FastAPI + React | B1 (Basic) |
| Database for PostgreSQL | Managed database | Basic |
| Monitor | Logging & metrics | Free tier |
| Application Insights | APM & tracing | Free tier |
| Container Registry | Docker images | Basic |

### 4.2 Containerization: Docker

```dockerfile
# Dockerfile (Multi-stage)
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build backend
FROM python:3.11-slim AS backend-builder
WORKDIR /app/backend
RUN pip install poetry
COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Stage 3: Production
FROM python:3.11-slim AS production
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/ ./backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Environment
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.3 CI/CD: GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd backend && pip install -r requirements-dev.txt
          cd ../frontend && npm ci
      
      - name: Run backend tests
        run: cd backend && pytest --cov=app --cov-report=xml
      
      - name: Run frontend tests
        run: cd frontend && npm run test:ci
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.ACR_LOGIN_SERVER }}/user-mgmt-portal:${{ github.sha }}
            ${{ secrets.ACR_LOGIN_SERVER }}/user-mgmt-portal:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v3
        with:
          app-name: 'ump-production'
          images: '${{ secrets.ACR_LOGIN_SERVER }}/user-mgmt-portal:${{ github.sha }}'
```

---

## 5. Version Compatibility Matrix

| Component | Version | Compatible With | Notes |
|-----------|---------|-----------------|-------|
| React | 18.2.0 | TypeScript 5.x | Concurrent features require strict mode |
| TypeScript | 5.3.3 | React 18, Vite 5 | Strict config enforced |
| Vite | 5.0.0 | React 18, TypeScript 5 | SWC for fast builds |
| Tailwind | 3.4.0 | PostCSS 8 | JIT mode enabled |
| FastAPI | 0.109.0 | Python 3.10+ | Pydantic v2 required |
| SQLAlchemy | 2.0.25 | Python 3.9+ | Async ORM patterns |
| PostgreSQL | 15.x | SQLAlchemy 2.0 | JSONB, UUID extensions |
| Python | 3.11.7 | All backend deps | Performance improvements |

---

## 6. Decision Log

| ID | Decision | Date | Rationale |
|----|----------|------|-----------|
| TECH-001 | React 18 over Vue/Angular | 2024-01 | Team expertise, ecosystem size |
| TECH-002 | FastAPI over Django | 2024-01 | Performance, async, auto-docs |
| TECH-003 | PostgreSQL over MySQL | 2024-01 | JSONB, full-text search |
| TECH-004 | Zustand over Redux | 2024-01 | Simplicity, less boilerplate |
| TECH-005 | React Query over SWR | 2024-01 | Mutation handling, devtools |
| TECH-006 | Azure over AWS/GCP | 2024-01 | Existing org relationship |

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-25  
**Owner**: System Architect
