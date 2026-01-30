# Action Plan for Friday, January 31, 2026

**Current Status:** 85% production-ready (post-audit fixes)
**Goal:** 100% production-ready and deployed to staging
**Total Time:** 3-4 hours

---

## Morning Session (1 hour) - Critical Path to Deployable

### ✅ Prerequisites Check (5 min)

**1. Verify Docker Desktop is installed**
```powershell
docker --version
docker-compose --version
```

If not installed:
- Download: https://www.docker.com/products/docker-desktop
- Install Docker Desktop for Windows
- Restart computer
- Verify installation

**2. Verify backend dependencies installed**
```powershell
cd backend
python -m pip list | grep -E "sentry-sdk|prometheus"
```

Should see:
- sentry-sdk==2.20.0
- prometheus-fastapi-instrumentator==7.0.0

If missing:
```powershell
python -m pip install -r requirements.txt
```

**3. Verify frontend dependencies installed**
```powershell
cd frontend
npm list @sentry/react
```

Should see: @sentry/react@2.x.x

If missing:
```powershell
npm install @sentry/react
```

---

### 🐳 Task 1: Test Docker Build (15 min)

**Objective:** Verify Docker configuration actually works

**Steps:**
```powershell
cd C:\Users\User\tokenlab-ui-clean-react

# Test build backend only (faster)
docker-compose build backend
```

**Expected outcome:**
- Build succeeds without errors
- See: "Successfully tagged tokenlab-backend:latest" or similar

**If it fails:**
- Read error message carefully
- Common issues:
  - Missing dependencies in requirements.txt → add them
  - Wrong Python version → use Python 3.11 in Dockerfile
  - Path issues → check COPY commands in Dockerfile
- Fix and retry

**Document result:**
```powershell
# Create build log
docker-compose build backend 2>&1 | Tee-Object -FilePath build_log.txt
```

**Time check:** Should take 5-10 minutes
**Blocker:** If fails, must fix before continuing

---

### 🏥 Task 2: Verify Health Checks (10 min)

**Objective:** Ensure health endpoint works as Docker expects

**Start backend locally:**
```powershell
cd backend
python -m app.main
```

**In another terminal, test health endpoint:**
```powershell
# Test backend health
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "...", ...}

# Test metrics endpoint (Prometheus)
curl http://localhost:8000/metrics

# Expected: Prometheus metrics output (text format)
```

**Verify format matches Docker health check:**
```dockerfile
# From Dockerfile.backend
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

**If health check fails:**
- Check response format in `backend/app/api/routes/health.py`
- Ensure it returns 200 status code
- Verify JSON format is valid

**Document result:**
```powershell
curl http://localhost:8000/health | Out-File -FilePath health_check_result.json
curl http://localhost:8000/metrics | Out-File -FilePath metrics_result.txt
```

**Time check:** 5-10 minutes
**Blocker:** Health check must return 200 OK

---

### 🔐 Task 3: Set Up Sentry Account (10 min)

**Objective:** Get real Sentry DSN for error tracking

**Steps:**

1. **Sign up for Sentry**
   - Go to: https://sentry.io/signup/
   - Use work email
   - Free tier is fine for testing

2. **Create Backend Project**
   - Click "Create Project"
   - Platform: Python
   - Alert frequency: Default
   - Project name: "tokenlab-backend"
   - Copy DSN (looks like: https://abc123@o456.ingest.us.sentry.io/789)

3. **Create Frontend Project**
   - Click "Create Project" again
   - Platform: React
   - Project name: "tokenlab-frontend"
   - Copy DSN (different from backend)

4. **Update environment files**

`.env.production`:
```bash
# Backend
SENTRY_DSN=https://YOUR_BACKEND_KEY@o0.ingest.us.sentry.io/PROJECT_ID
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
```

`frontend/.env.production`:
```bash
# Frontend
VITE_API_URL=http://localhost:8000
VITE_SENTRY_DSN=https://YOUR_FRONTEND_KEY@o0.ingest.us.sentry.io/PROJECT_ID
VITE_ENVIRONMENT=staging
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

5. **Test Sentry integration**
```powershell
# Set DSN temporarily
$env:SENTRY_DSN="your_backend_dsn_here"

# Start backend
cd backend
python -m app.main

# Should see: "[OK] Sentry initialized for staging"
```

**Time check:** 10 minutes
**Can skip:** If just testing, but needed for production

---

### 🚀 Task 4: Deploy with PowerShell Script (10 min)

**Objective:** Use the Windows deployment script

**Steps:**
```powershell
cd C:\Users\User\tokenlab-ui-clean-react

# Run deployment script
.\deploy.ps1
```

**The script will:**
1. Check if .env.production exists (create if not)
2. Install backend dependencies
3. Build Docker images
4. Start all services
5. Run health checks
6. Display access URLs

**Expected output:**
```
✨ Deployment Complete!

📊 Access Points:
   - Frontend:   http://localhost
   - Backend:    http://localhost:8000
   - API Docs:   http://localhost:8000/docs
   - Metrics:    http://localhost:8000/metrics
   - Prometheus: http://localhost:9090
   - Grafana:    http://localhost:3000
```

**If it fails:**
- Read error messages
- Check Docker is running
- Check ports aren't in use: `netstat -ano | findstr ":8000"`
- Fix and retry

**Verify deployment:**
```powershell
# Check running containers
docker-compose ps

# Should see:
# tokenlab-backend   running   Healthy
# tokenlab-frontend  running   Healthy

# Check logs
docker-compose logs backend | Select-Object -Last 20
docker-compose logs frontend | Select-Object -Last 20
```

**Time check:** 10 minutes (5 min build, 5 min startup)
**Blocker:** If fails, review Docker logs

---

### ✅ Morning Checkpoint

**After 1 hour, you should have:**
- [x] Docker build succeeding
- [x] Health checks passing
- [x] Sentry account created (optional but recommended)
- [x] Application deployed locally via Docker
- [x] All services showing "Healthy" status

**Verify with:**
```powershell
# Frontend
curl http://localhost/

# Backend API
curl http://localhost:8000/health

# Prometheus metrics
curl http://localhost:8000/metrics

# API docs
start http://localhost:8000/docs
```

**If all pass:** ✅ Application is DEPLOYABLE
**If any fail:** ❌ Fix before continuing

---

## Afternoon Session (2-3 hours) - Path to Confident

### 📊 Task 5: Run Load Tests (30 min)

**Objective:** Verify performance under concurrent load

**Install Locust:**
```powershell
pip install locust
```

**Start backend if not running:**
```powershell
cd backend
python -m app.main
# Or use Docker: docker-compose up -d backend
```

**Run load test (headless mode):**
```powershell
cd C:\Users\User\tokenlab-ui-clean-react

# Test with 10 users (warm-up)
locust -f load-tests/locustfile.py `
       --host=http://localhost:8000 `
       --users 10 `
       --spawn-rate 2 `
       --run-time 1m `
       --headless `
       --html load_test_10users.html

# Test with 50 users (realistic load)
locust -f load-tests/locustfile.py `
       --host=http://localhost:8000 `
       --users 50 `
       --spawn-rate 10 `
       --run-time 3m `
       --headless `
       --html load_test_50users.html

# Test with 100 users (stress test)
locust -f load-tests/locustfile.py `
       --host=http://localhost:8000 `
       --users 100 `
       --spawn-rate 10 `
       --run-time 5m `
       --headless `
       --html load_test_100users.html
```

**Expected results:**

| Metric | 10 Users | 50 Users | 100 Users |
|--------|----------|----------|-----------|
| RPS | 5-10 | 20-40 | 40-80 |
| P95 Latency | <500ms | <1s | <2s |
| Failure Rate | <1% | <2% | <5% |
| Avg Response Time | <200ms | <500ms | <1s |

**Analyze results:**
```powershell
# Open HTML report
start load_test_100users.html

# Check for:
# - Failures (should be <5%)
# - 95th percentile latency
# - Requests per second
# - Any error patterns
```

**If performance is poor:**
- Check CPU/memory usage: `docker stats`
- Review error logs: `docker-compose logs backend`
- Consider adding workers: Update docker-compose.yml to use `--workers 4`
- Tune rate limits in backend/app/main.py

**Document results:**
```powershell
# Save results
mkdir load_test_results
Move-Item *.html load_test_results/

# Create summary
@"
Load Test Results ($(Get-Date -Format 'yyyy-MM-dd'))

10 Users:  [RPS] [P95] [Failures]
50 Users:  [RPS] [P95] [Failures]
100 Users: [RPS] [P95] [Failures]

Notes: [Any issues or observations]
"@ | Out-File -FilePath load_test_results/summary.txt
```

**Time check:** 30 minutes
**Can skip:** If time-constrained, but needed for production confidence

---

### 🧪 Task 6: Fix Critical Frontend Tests (2 hours)

**Objective:** Fix highest-value failing tests

**Priority order:**
1. App.test.tsx integration tests (7 failing)
2. ABMWorkflow.test.tsx (22 failing) - only if time permits

**Focus on App.test.tsx first:**
```powershell
cd frontend
npm test src/App.test.tsx -- --run --reporter=verbose
```

**Common failure patterns:**

**Pattern 1: "Unable to find element"**
```typescript
// FAILING:
expect(screen.getByText('Running ABM Simulation')).toBeInTheDocument()

// FIX: Check actual text in App.tsx, might be different
expect(screen.getByText(/Running.*Simulation/i)).toBeInTheDocument()
```

**Pattern 2: "Expected element to have attribute"**
```typescript
// FAILING:
expect(tab).toHaveAttribute('data-state', 'active')

// FIX: Wait for state change
await waitFor(() => {
  expect(tab).toHaveAttribute('data-state', 'active')
})
```

**Pattern 3: "Function not called"**
```typescript
// FAILING:
expect(mockSubmit).toHaveBeenCalledTimes(1)

// FIX: Ensure event is triggered
fireEvent.click(submitButton)
await waitFor(() => {
  expect(mockSubmit).toHaveBeenCalledTimes(1)
})
```

**Strategy:**
1. Fix one test at a time
2. Run test after each fix
3. Don't move to next until current passes
4. Document why it was failing

**Create test fix log:**
```powershell
@"
Test Fix Log - $(Get-Date -Format 'yyyy-MM-dd')

Test: [test name]
Failure: [why it failed]
Fix: [what you changed]
Result: [pass/fail]

---
"@ | Out-File -FilePath test_fixes.txt
```

**Time check:** 2 hours (aim for 7 tests, ~17 min each)
**Can skip:** If time-constrained, but aim for at least 3-4 fixes

**Track progress:**
```powershell
# Before
npm test -- --run | Select-String "Tests.*failed"
# Should see: "30 failed"

# After each fix
npm test -- --run | Select-String "Tests.*failed"
# Goal: "20 failed" or fewer
```

---

### ✅ Afternoon Checkpoint

**After 3 hours, you should have:**
- [x] Load test results documented
- [x] Performance baseline established
- [x] At least 5-7 frontend tests fixed
- [x] Test failure count reduced from 30 → 23-25

**Quality check:**
```powershell
# Run all tests
cd frontend
npm test -- --run

# Check results
# Before: 104 passed, 30 failed
# After:  110+ passed, 23-25 failed
```

---

## End of Day Deliverables

### Documentation to Create

**1. Deployment Verification Report**
```powershell
@"
Deployment Verification - $(Get-Date -Format 'yyyy-MM-dd')

✅ VERIFIED:
- [ ] Docker build succeeds
- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] Prometheus /metrics endpoint works
- [ ] Sentry account created and DSN configured
- [ ] deploy.ps1 script works

⚠️ ISSUES FOUND:
- [List any issues]

📊 PERFORMANCE:
- 10 users:  [RPS], [P95], [Failures]
- 50 users:  [RPS], [P95], [Failures]
- 100 users: [RPS], [P95], [Failures]

🧪 TESTS:
- Backend: 120/122 passing (98%)
- Frontend: [X]/134 passing ([Y]%)

📝 NOTES:
- [Any observations]
"@ | Out-File -FilePath DEPLOYMENT_VERIFICATION.txt
```

**2. Production Readiness Checklist**
```powershell
@"
Production Readiness Checklist - $(Get-Date -Format 'yyyy-MM-dd')

SECURITY:
- [x] 0 vulnerabilities (pip-audit verified)
- [x] Dependencies updated
- [x] Security headers configured (nginx.conf)
- [x] Rate limiting enabled (slowapi)

MONITORING:
- [x] Sentry integrated in code
- [x] Prometheus integrated in code
- [x] Health checks working
- [ ] Sentry DSN configured in production
- [ ] Grafana dashboards created

DEPLOYMENT:
- [x] Docker configuration complete
- [ ] Docker build tested and passing
- [x] Windows deployment script (deploy.ps1)
- [ ] Rollback procedure tested

TESTING:
- [x] Backend tests: 120/122 (98%)
- [ ] Frontend tests: [X]/134 ([Y]%)
- [ ] Load tests run
- [ ] Performance acceptable

OPERATIONS:
- [x] Logging with rotation configured
- [ ] Alert rules configured
- [ ] On-call rotation defined
- [ ] Incident response plan documented

READY FOR PRODUCTION: [ ] YES / [ ] NO (needs: [list])
"@ | Out-File -FilePath PRODUCTION_READINESS.txt
```

---

## Success Criteria

### Minimum (Deployable to Staging)
- [x] Docker build succeeds
- [x] Health checks pass
- [x] Application starts without errors
- [x] Basic functionality works (can submit simulation)
- [x] Monitoring integrated (even if DSN not set)

### Target (Confident for Production)
- [x] All minimum criteria
- [x] Load tests run and performance acceptable
- [x] Sentry DSN configured and errors captured
- [x] Frontend tests >85% passing (110+/134)
- [x] Prometheus metrics working
- [x] Documentation complete

### Stretch (Production-Ready)
- [x] All target criteria
- [x] Frontend tests >90% passing (120+/134)
- [x] Load tests show <1% error rate at 100 users
- [x] Grafana dashboards created
- [x] Alert rules configured
- [x] Rollback tested

---

## Contingency Plans

### If Docker Build Fails
**Symptoms:** Build errors, dependency issues
**Fallback:** Run locally without Docker
```powershell
# Backend
cd backend
python -m uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm run dev
```
**Impact:** Can still test and fix issues, deploy Docker later

### If Load Tests Fail
**Symptoms:** Script errors, import failures
**Fallback:** Manual testing with curl
```powershell
# Test simulation endpoint manually
$body = Get-Content test-config.json
Invoke-WebRequest -Uri "http://localhost:8000/api/v2/abm/simulate" `
                  -Method POST `
                  -ContentType "application/json" `
                  -Body $body
```
**Impact:** Can still verify functionality, optimize later

### If Frontend Tests Too Hard to Fix
**Symptoms:** 2+ hours spent, still many failing
**Fallback:** Focus on manual testing
- Test each user flow manually
- Document what works
- Create issues for failing tests
- Deploy anyway if functionality verified
**Impact:** Lower confidence, but can still deploy

### If Sentry Signup Issues
**Symptoms:** Email verification delay, signup errors
**Fallback:** Skip Sentry for now
- Deploy without DSN
- Monitor logs manually
- Set up Sentry next week
**Impact:** No automatic error tracking, but can still deploy

---

## Timeline Summary

| Time | Task | Duration | Status |
|------|------|----------|--------|
| 9:00 AM | Prerequisites check | 5 min | [ ] |
| 9:05 AM | Test Docker build | 15 min | [ ] |
| 9:20 AM | Verify health checks | 10 min | [ ] |
| 9:30 AM | Set up Sentry account | 10 min | [ ] |
| 9:40 AM | Deploy with deploy.ps1 | 10 min | [ ] |
| 9:50 AM | Morning break | 10 min | [ ] |
| 10:00 AM | **CHECKPOINT: Deployable** | - | [ ] |
| 10:00 AM | Run load tests | 30 min | [ ] |
| 10:30 AM | Analyze results | 15 min | [ ] |
| 10:45 AM | Start fixing tests | 2 hr | [ ] |
| 12:45 PM | Lunch break | 45 min | [ ] |
| 1:30 PM | Continue fixing tests | 45 min | [ ] |
| 2:15 PM | **CHECKPOINT: Confident** | - | [ ] |
| 2:15 PM | Create documentation | 30 min | [ ] |
| 2:45 PM | Final verification | 15 min | [ ] |
| 3:00 PM | **COMPLETE** | - | [ ] |

**Total active time:** 3.5 hours
**With breaks:** 6 hours (9 AM - 3 PM)

---

## Emergency Contacts / Resources

**If stuck:**
- Docker Desktop docs: https://docs.docker.com/desktop/windows/
- Sentry docs: https://docs.sentry.io/platforms/python/
- Locust docs: https://docs.locust.io/
- Previous work: Read HONEST_AUDIT.md for context
- Stack Overflow: Search for specific error messages

**Files to reference:**
- `HONEST_AUDIT.md` - What was wrong and why
- `ACTUAL_STATUS.md` - Current real status
- `DEPLOYMENT_GUIDE.md` - How to deploy
- `ROLLBACK_PROCEDURE.md` - How to rollback
- `MONITORING_SETUP.md` - How to set up monitoring

---

## Final Notes

**What's realistic to complete:**
- ✅ Docker build and deployment (1 hour) - DEFINITELY ACHIEVABLE
- ✅ Load testing (30 min) - DEFINITELY ACHIEVABLE
- ⚠️ Fixing all 30 tests (2 hours) - AMBITIOUS, aim for 50% (15 tests)

**What's the bare minimum:**
- Docker build works
- App deploys via deploy.ps1
- Health checks pass
- Basic load test runs

**What would make you confident:**
- All of above PLUS
- Sentry DSN configured
- Load tests show good performance
- At least 10 tests fixed (reducing failures to ~20)

**Good luck! 🚀**

Remember: Done is better than perfect. Get it working first, optimize later.
