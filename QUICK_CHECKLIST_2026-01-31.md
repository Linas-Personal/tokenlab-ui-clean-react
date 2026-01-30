# Quick Checklist - Friday, Jan 31, 2026

Print this page and check off as you go. 📋

---

## Morning (1 hour) - Get to Deployable

### ☐ Step 1: Prerequisites (5 min)
```powershell
docker --version          # Should show version
cd backend
python -m pip list | grep sentry  # Should show sentry-sdk==2.20.0
cd ../frontend
npm list @sentry/react    # Should show @sentry/react
```

### ☐ Step 2: Test Docker Build (15 min)
```powershell
cd C:\Users\User\tokenlab-ui-clean-react
docker-compose build backend
# Expected: "Successfully tagged..."
```
**If fails:** Read error, fix, retry

### ☐ Step 3: Test Health Checks (10 min)
```powershell
cd backend
python -m app.main
# In another terminal:
curl http://localhost:8000/health  # Should return {"status": "healthy"}
curl http://localhost:8000/metrics # Should return Prometheus metrics
```

### ☐ Step 4: Sentry Account (10 min)
- Go to https://sentry.io/signup/
- Create backend project → copy DSN
- Create frontend project → copy DSN
- Edit `.env.production` and `frontend/.env.production`

### ☐ Step 5: Deploy (10 min)
```powershell
.\deploy.ps1
# Expected: "✨ Deployment Complete!"
# Verify: curl http://localhost
```

### ✅ CHECKPOINT: Can you access http://localhost?
- **YES** → Continue to Afternoon
- **NO** → Debug with `docker-compose logs`

---

## Afternoon (2-3 hours) - Get to Confident

### ☐ Step 6: Load Tests (30 min)
```powershell
pip install locust

# Quick test (1 min)
locust -f load-tests/locustfile.py --host=http://localhost:8000 `
       --users 10 --spawn-rate 2 --run-time 1m --headless

# Realistic test (3 min)
locust -f load-tests/locustfile.py --host=http://localhost:8000 `
       --users 50 --spawn-rate 10 --run-time 3m --headless `
       --html load_test_50users.html

# Stress test (5 min)
locust -f load-tests/locustfile.py --host=http://localhost:8000 `
       --users 100 --spawn-rate 10 --run-time 5m --headless `
       --html load_test_100users.html
```
**Check:** Open `load_test_100users.html` - failures should be <5%

### ☐ Step 7: Fix Frontend Tests (2 hours)
```powershell
cd frontend
npm test src/App.test.tsx -- --run --reporter=verbose

# Fix tests one at a time
# After each fix, run: npm test src/App.test.tsx -- --run
```
**Goal:** Fix at least 5-10 tests
**Before:** 30 failed
**After:** 20-25 failed

### ✅ CHECKPOINT: Are load tests <5% failures?
- **YES** → Good performance
- **NO** → Check CPU/memory with `docker stats`

---

## End of Day

### ☐ Step 8: Document Results (30 min)
```powershell
# Create summary
@"
Results - $(Get-Date -Format 'yyyy-MM-dd')

DOCKER:
- Build: [SUCCESS/FAIL]
- Deploy: [SUCCESS/FAIL]
- Health: [PASS/FAIL]

LOAD TESTS:
- 50 users: [RPS], [P95], [Failures %]
- 100 users: [RPS], [P95], [Failures %]

TESTS:
- Backend: 120/122 (98%)
- Frontend: [X]/134 ([Y]%)

READY: [YES/NO]
"@ | Out-File -FilePath RESULTS.txt
```

### ✅ FINAL: Production Ready?
- **Minimum (Deployable):**
  - [ ] Docker build works
  - [ ] App accessible at http://localhost
  - [ ] Health checks pass

- **Target (Confident):**
  - [ ] All minimum +
  - [ ] Load tests <5% failures
  - [ ] Frontend tests >85% (110+/134)

- **Stretch (Production):**
  - [ ] All target +
  - [ ] Frontend tests >90% (120+/134)
  - [ ] Sentry DSN configured

---

## Quick Commands Reference

**Start everything:**
```powershell
.\deploy.ps1
```

**Check status:**
```powershell
docker-compose ps
docker-compose logs -f
```

**Stop everything:**
```powershell
docker-compose down
```

**Restart one service:**
```powershell
docker-compose restart backend
docker-compose logs -f backend
```

**Run tests:**
```powershell
cd backend && pytest tests/ -v
cd frontend && npm test -- --run
```

**View metrics:**
- Frontend: http://localhost
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

---

## If Something Breaks

**Docker won't start:**
```powershell
# Check if Docker Desktop is running
# Restart Docker Desktop
# Try: docker-compose down && docker-compose up -d
```

**Port already in use:**
```powershell
# Find what's using port 8000
netstat -ano | findstr ":8000"
# Kill the process or use different port
```

**Health check failing:**
```powershell
# Check logs
docker-compose logs backend | Select-Object -Last 50
# Verify endpoint manually
curl http://localhost:8000/health
```

**Tests timing out:**
```powershell
# Increase timeout in test files
# Or run tests individually
npm test src/App.test.tsx -- --run --testTimeout=30000
```

---

**Time budget:**
- Morning: 1 hour (critical path)
- Afternoon: 2-3 hours (quality improvements)
- **Total: 3-4 hours**

**Remember:** Perfect is the enemy of done. Get it working, then make it better. 🚀
