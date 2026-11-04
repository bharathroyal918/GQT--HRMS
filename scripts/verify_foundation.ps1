<#
.SYNOPSIS
    Automated Phase 1 Quality Gate and Invariant Verification Script for GQT HRMS.
.DESCRIPTION
    Validates backend Django checks, database migrations, pytest suite with coverage,
    OpenAPI schema generation, frontend TypeScript compile, vitest tests, and Vite build.
#>

$ErrorActionPreference = "Stop"
$WorkspaceRoot = (Get-Location).Path
$BackendPython = Join-Path $WorkspaceRoot "backend\.venv\Scripts\python.exe"
$BackendPytest = Join-Path $WorkspaceRoot "backend\.venv\Scripts\pytest.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " GQT HRMS Platform - Quality Gates & Verification" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$SuccessCount = 0
$TotalGates = 7

# Gate 1: Django System Check
Write-Host "`n[Gate 1/7] Running Django system diagnostics..." -ForegroundColor Yellow
& $BackendPython backend\manage.py check --settings=config.settings.local
if ($LASTEXITCODE -eq 0) {
    Write-Host " PASS: Django system check clean (0 issues)." -ForegroundColor Green
    $SuccessCount++
} else {
    Write-Host " FAIL: Django system check failed." -ForegroundColor Red
    exit 1
}

# Gate 2: Database Migration Drift
Write-Host "`n[Gate 2/7] Checking for unapplied model changes / migration drift..." -ForegroundColor Yellow
& $BackendPython backend\manage.py makemigrations --check --dry-run --settings=config.settings.local
if ($LASTEXITCODE -eq 0) {
    Write-Host " PASS: Zero model/migration schema drift detected." -ForegroundColor Green
    $SuccessCount++
} else {
    Write-Host " FAIL: Model schema drift detected! Run makemigrations." -ForegroundColor Red
    exit 1
}

# Gate 3: Pytest Suite & Coverage
Write-Host "`n[Gate 3/7] Executing backend pytest test suite..." -ForegroundColor Yellow
& $BackendPytest -c backend\pytest.ini backend\tests --cov=apps --cov-report=term-missing
if ($LASTEXITCODE -eq 0) {
    Write-Host " PASS: All backend unit & integration tests passed." -ForegroundColor Green
    $SuccessCount++
} else {
    Write-Host " FAIL: Pytest suite had failures." -ForegroundColor Red
    exit 1
}

# Gate 4: OpenAPI 3.1 Schema Export
Write-Host "`n[Gate 4/7] Generating OpenAPI 3.1 specification..." -ForegroundColor Yellow
& $BackendPython backend\manage.py spectacular --file backend\openapi-schema.yaml --settings=config.settings.local
if ($LASTEXITCODE -eq 0 -and (Test-Path backend\openapi-schema.yaml)) {
    Write-Host " PASS: OpenAPI 3.1 specification generated cleanly." -ForegroundColor Green
    $SuccessCount++
} else {
    Write-Host " FAIL: OpenAPI schema generation failed." -ForegroundColor Red
    exit 1
}

# Gate 5: Frontend TypeScript Strict Check
Write-Host "`n[Gate 5/7] Running frontend TypeScript strict check (tsc -b --noEmit)..." -ForegroundColor Yellow
Push-Location frontend
try {
    npm run lint
    if ($LASTEXITCODE -eq 0) {
        Write-Host " PASS: Frontend TypeScript strict compile clean (0 errors)." -ForegroundColor Green
        $SuccessCount++
    } else {
        Write-Host " FAIL: TypeScript errors found." -ForegroundColor Red
        Pop-Location
        exit 1
    }

    # Gate 6: Frontend Vitest Suite
    Write-Host "`n[Gate 6/7] Running frontend Vitest test suite..." -ForegroundColor Yellow
    npm test
    if ($LASTEXITCODE -eq 0) {
        Write-Host " PASS: All frontend Vitest tests passed." -ForegroundColor Green
        $SuccessCount++
    } else {
        Write-Host " FAIL: Vitest test suite had failures." -ForegroundColor Red
        Pop-Location
        exit 1
    }

    # Gate 7: Frontend Production Bundle Build
    Write-Host "`n[Gate 7/7] Executing frontend Vite production build..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -eq 0 -and (Test-Path dist\index.html)) {
        Write-Host " PASS: Frontend production bundle successfully generated in dist/." -ForegroundColor Green
        $SuccessCount++
    } else {
        Write-Host " FAIL: Frontend production build failed." -ForegroundColor Red
        Pop-Location
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " SUMMARY: All $SuccessCount of $TotalGates Quality Gates Passed Successfully!" -ForegroundColor Green
Write-Host " Phase 1 Foundation & Architecture Verification COMPLETE." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
