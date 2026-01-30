#!/bin/bash
set -e

echo "🚀 TokenLab Production Deployment Script"
echo "========================================"
echo ""

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "⚠️  .env.production not found!"
    echo "📋 Creating from template..."
    cp .env.production.example .env.production
    echo ""
    echo "✏️  Please edit .env.production and add your Sentry DSN:"
    echo "   - Get DSN from https://sentry.io"
    echo "   - Add backend DSN to SENTRY_DSN"
    echo "   - Add frontend DSN to VITE_SENTRY_DSN"
    echo ""
    echo "Press ENTER when ready to continue..."
    read
fi

echo "1️⃣  Installing backend dependencies..."
cd backend && pip install -r requirements.txt --quiet
cd ..

echo "2️⃣  Building Docker images..."
docker-compose build

echo "3️⃣  Starting services..."
docker-compose up -d

echo "4️⃣  Waiting for services to be ready..."
sleep 5

echo "5️⃣  Running health checks..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/health | grep -c "healthy" || echo "0")
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80)

if [ "$BACKEND_HEALTH" = "1" ]; then
    echo "   ✅ Backend healthy"
else
    echo "   ❌ Backend not responding"
    exit 1
fi

if [ "$FRONTEND_HEALTH" = "200" ]; then
    echo "   ✅ Frontend healthy"
else
    echo "   ❌ Frontend not responding"
    exit 1
fi

echo ""
echo "✨ Deployment Complete!"
echo ""
echo "📊 Access Points:"
echo "   - Frontend:   http://localhost"
echo "   - Backend:    http://localhost:8000"
echo "   - API Docs:   http://localhost:8000/docs"
echo "   - Metrics:    http://localhost:8000/metrics"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana:    http://localhost:3000"
echo ""
echo "📝 Next Steps:"
echo "   1. Monitor logs: docker-compose logs -f"
echo "   2. Run load tests: pip install locust && locust -f load-tests/locustfile.py"
echo "   3. Check Sentry for errors: https://sentry.io"
echo ""
