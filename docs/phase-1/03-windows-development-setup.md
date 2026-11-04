# GQT HRMS & Recruitment CRM Platform — Phase 1: Windows Development Setup

## 1. Prerequisites

The development environment requires:
- Windows 10/11 x64
- PowerShell 7+ or Windows PowerShell 5.1
- Python 3.12+ (Python 3.14.7 installed on host)
- `uv` package installer (`uv venv` and `uv pip`)
- Node.js v20+ (Node v24.21.0, npm 11.19.0 installed on host)
- Git 2.40+

---

## 2. Backend Setup

### 2.1 Virtual Environment & Dependencies
```powershell
# Navigate to repository root
cd "C:\Users\User\Documents\GQT HRMS"

# Create virtual environment using uv
uv venv backend\.venv --seed

# Install backend dependencies
uv pip install -r backend\requirements.txt --python backend\.venv\Scripts\python.exe
```

### 2.2 Local Database Initialization
```powershell
# Run migrations on local SQLite dev database
& backend\.venv\Scripts\python.exe backend\manage.py migrate --settings=config.settings.local

# Run Django system check
& backend\.venv\Scripts\python.exe backend\manage.py check --settings=config.settings.local
```

### 2.3 Running Backend Tests
```powershell
# Run pytest test suite with coverage
& backend\.venv\Scripts\pytest.exe backend\tests --cov=apps --cov-report=term-missing
```

### 2.4 Running the Local API Server
```powershell
& backend\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```
The API is available at:
- Health probe: `http://127.0.0.1:8000/api/v1/health/`
- Readiness probe: `http://127.0.0.1:8000/api/v1/ready/`
- Swagger UI: `http://127.0.0.1:8000/api/v1/schema/swagger/`
- Redoc: `http://127.0.0.1:8000/api/v1/schema/redoc/`

---

## 3. Frontend Setup

### 3.1 Install Dependencies
```powershell
cd "C:\Users\User\Documents\GQT HRMS\frontend"
npm install
```

### 3.2 Running Quality Checks
```powershell
# TypeScript strict type-check
npm run lint

# Component & layout Vitest suite
npm test

# Production build
npm run build
```

### 3.3 Running the Vite Development Server
```powershell
npm run dev
```
The application will be served at `http://localhost:5173`. Proxied API requests to `/api/*` are routed to `http://127.0.0.1:8000`.

---

## 4. One-Click Foundation Quality Gate Verification

To run all 7 automated quality gates across backend and frontend in a single command:
```powershell
cd "C:\Users\User\Documents\GQT HRMS"
powershell -ExecutionPolicy Bypass -File scripts\verify_foundation.ps1
```
All 7 gates will execute sequentially and verify:
1. Django system diagnostics
2. Model schema drift
3. Backend pytest unit/integration tests with coverage
4. OpenAPI 3.1 schema export
5. Frontend TypeScript strict compile
6. Frontend Vitest suite
7. Frontend Vite production build

