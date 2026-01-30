# TokenLab Production Deployment Script (PowerShell for Windows)
# Usage: .\deploy.ps1

Write-Host "🚀 TokenLab Production Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env.production exists
if (-not (Test-Path ".env.production")) {
    Write-Host "⚠️  .env.production not found!" -ForegroundColor Yellow
    Write-Host "📋 Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.production.example" ".env.production"
    Write-Host ""
    Write-Host "✏️  Please edit .env.production and add your Sentry DSN:" -ForegroundColor Yellow
    Write-Host "   - Get DSN from https://sentry.io"
    Write-Host "   - Add backend DSN to SENTRY_DSN"
    Write-Host "   - Add frontend DSN to VITE_SENTRY_DSN"
    Write-Host ""
    Write-Host "Press ENTER when ready to continue..."
    Read-Host
}

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not found! Please install Docker Desktop:" -ForegroundColor Red
    Write-Host "   https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker-compose not found! Please install Docker Desktop:" -ForegroundColor Red
    Write-Host "   https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

Write-Host "1️⃣  Installing backend dependencies..." -ForegroundColor Green
Push-Location backend
python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

Write-Host "2️⃣  Building Docker images..." -ForegroundColor Green
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "3️⃣  Starting services..." -ForegroundColor Green
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host "4️⃣  Waiting for services to be ready..." -ForegroundColor Green
Start-Sleep -Seconds 5

Write-Host "5️⃣  Running health checks..." -ForegroundColor Green

# Backend health check
try {
    $backendHealth = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction Stop
    if ($backendHealth.Content -like "*healthy*") {
        Write-Host "   ✅ Backend healthy" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Backend not responding correctly" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Backend not responding" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

# Frontend health check
try {
    $frontendHealth = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -ErrorAction Stop
    if ($frontendHealth.StatusCode -eq 200) {
        Write-Host "   ✅ Frontend healthy" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Frontend not responding" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Frontend not responding" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✨ Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Access Points:" -ForegroundColor Cyan
Write-Host "   - Frontend:   http://localhost" -ForegroundColor White
Write-Host "   - Backend:    http://localhost:8000" -ForegroundColor White
Write-Host "   - API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "   - Metrics:    http://localhost:8000/metrics" -ForegroundColor White
Write-Host "   - Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "   - Grafana:    http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Monitor logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   2. Run load tests: pip install locust && locust -f load-tests/locustfile.py" -ForegroundColor White
Write-Host "   3. Check Sentry for errors: https://sentry.io" -ForegroundColor White
Write-Host ""

# Optional: Open browser
$openBrowser = Read-Host "Open frontend in browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost"
}
