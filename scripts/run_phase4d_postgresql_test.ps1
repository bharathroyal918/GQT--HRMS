# ==============================================================================
# GQT HRMS — Phase 4D: Automated Isolated PostgreSQL Concurrency Test Harness
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "=== Step 1: Checking Docker and Port 5433 ==="
docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker daemon is not running. Aborting."
    exit 1
}

$existingConnection = Get-NetTCPConnection -LocalPort 5433 -ErrorAction SilentlyContinue
if ($existingConnection) {
    Write-Error "Port 5433 is currently occupied. Aborting."
    exit 1
}

$existingContainer = docker ps -a --filter "name=gqt_hrms_phase4d_pg" --format "{{.Names}}"
if ($existingContainer -eq "gqt_hrms_phase4d_pg") {
    Write-Host "Removing pre-existing disposable container gqt_hrms_phase4d_pg..."
    docker rm -f gqt_hrms_phase4d_pg | Out-Null
}

Write-Host "=== Step 2: Provisioning Isolated PostgreSQL 16 Test Container ==="
$bytes = New-Object byte[] 24
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$randPass = [Convert]::ToBase64String($bytes) -replace '[^a-zA-Z0-9]','X'

$containerId = docker run -d `
    --name gqt_hrms_phase4d_pg `
    -e POSTGRES_DB=gqt_hrms_phase4d_test `
    -e POSTGRES_USER=postgres `
    -e POSTGRES_PASSWORD=$randPass `
    -p 5433:5432 `
    postgres:16-alpine

Write-Host "Container started: $containerId"

Write-Host "Waiting for PostgreSQL readiness on port 5433..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    docker exec gqt_hrms_phase4d_pg pg_isready -U postgres -d gqt_hrms_phase4d_test | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    docker rm -f gqt_hrms_phase4d_pg | Out-Null
    Write-Error "PostgreSQL failed to become ready in 30 seconds."
    exit 1
}

Write-Host "PostgreSQL is ready! Inspecting server version:"
docker exec gqt_hrms_phase4d_pg psql -U postgres -d gqt_hrms_phase4d_test -c "SELECT version();"

try {
    Write-Host "=== Step 3: Setting Test Environment and Diagnosing Backend ==="
    $env:POSTGRES_TEST_DATABASE_URL = "postgresql://postgres:$randPass@localhost:5433/gqt_hrms_phase4d_test"
    $env:DB_SSLMODE = "disable"
    $env:PYTHONPATH = "backend"

    backend\.venv\Scripts\python.exe -c @"
import os, sys, django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
django.setup()
from django.db import connection
print('=== Django Database Configuration Proof ===')
print('Database Vendor  :', connection.vendor)
print('Database Name    :', connection.settings_dict['NAME'])
print('Database Host    :', connection.settings_dict['HOST'])
print('Database Port    :', connection.settings_dict['PORT'])
assert connection.vendor == 'postgresql', 'Expected postgresql vendor!'
assert connection.settings_dict['PORT'] == 5433, 'Expected port 5433!'
print('Diagnostic Proof: VERIFIED (PostgreSQL on port 5433)')
"@

    Write-Host "`n=== Step 4: Running Focused Multi-Threaded Concurrency Test ==="
    backend\.venv\Scripts\pytest.exe -c backend\pytest.ini backend\tests\test_creatives.py -k test_threaded_concurrency_version_allocation -v --tb=short
    $concurrencyExit = $LASTEXITCODE

    Write-Host "`n=== Step 5: Running Complete Creative Studio Test Suite against PostgreSQL ==="
    backend\.venv\Scripts\pytest.exe -c backend\pytest.ini backend\tests\test_creatives.py -v --tb=short
    $creativesExit = $LASTEXITCODE

    Write-Host "`n=== Step 6: Running Full Backend Test Suite against PostgreSQL ==="
    backend\.venv\Scripts\pytest.exe -c backend\pytest.ini backend\tests -v --tb=short
    $fullSuiteExit = $LASTEXITCODE

    Write-Host "`n=== Results Summary ==="
    Write-Host "Concurrency Test Exit Code : $concurrencyExit"
    Write-Host "Creatives Suite Exit Code  : $creativesExit"
    Write-Host "Full Suite Exit Code       : $fullSuiteExit"

    if ($concurrencyExit -ne 0 -or $creativesExit -ne 0 -or $fullSuiteExit -ne 0) {
        Write-Error "One or more test suites failed."
    }
}
finally {
    Write-Host "`n=== Step 7: Cleaning Up Disposable Container ==="
    docker stop gqt_hrms_phase4d_pg | Out-Null
    docker rm gqt_hrms_phase4d_pg | Out-Null
    $env:POSTGRES_TEST_DATABASE_URL = ""
    $env:DB_SSLMODE = ""
    Write-Host "Disposable container gqt_hrms_phase4d_pg successfully stopped and removed."
}
