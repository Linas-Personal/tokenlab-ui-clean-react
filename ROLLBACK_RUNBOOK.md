# Rollback Runbook

**Purpose**: Step-by-step procedure to rollback to a previous stable version
**Owner**: DevOps/Engineering Team
**Last Updated**: 2026-01-26

---

## Quick Rollback (5 Minutes)

For immediate rollback to last known good version:

```bash
#!/bin/bash
# Quick Rollback Script

echo "🔄 Starting emergency rollback..."

# 1. Navigate to project
cd /path/to/tokenlab-ui-clean-react

# 2. Stop running services
echo "Stopping services..."
pkill -f "uvicorn"  # Backend
pkill -f "vite"     # Frontend (if running dev server)

# 3. Checkout last stable tag
echo "Rolling back to v1.0.0..."
git checkout v1.0.0

# 4. Reinstall dependencies
echo "Reinstalling dependencies..."
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 5. Restart services
echo "Restarting services..."
# Backend
cd backend && nohup python -m app.main > ../rollback_backend.log 2>&1 &
# Frontend (if applicable - usually pre-built for production)
cd ../frontend && nohup npm run dev > ../rollback_frontend.log 2>&1 &

echo "✅ Rollback complete"
echo "Check logs: rollback_backend.log, rollback_frontend.log"
```

---

## Rollback Scenarios

### Scenario 1: Bug in Latest Deployment

**Trigger**: New deployment has critical bug
**Time**: 5-10 minutes
**Risk**: Low

**Steps**:

1. **Identify Target Version**
   ```bash
   # List recent tags
   git tag -l --sort=-creatordate | head -5
   # Output: v1.0.0, v0.9.0, etc.
   ```

2. **Checkout Target**
   ```bash
   git checkout tags/v1.0.0
   ```

3. **Verify Tag**
   ```bash
   git log --oneline -1
   # Should show commit message for v1.0.0
   ```

4. **Reinstall Dependencies**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```

5. **Restart Services** (see Quick Rollback script)

6. **Verify Health**
   ```bash
   curl http://localhost:8000/api/v1/health
   # Expected: {"status": "healthy"}
   ```

7. **Notify Team**
   - Post in #incidents channel
   - Update status page
   - Log rollback in incident tracker

---

### Scenario 2: Database Schema Change Rollback

**Trigger**: Schema migration needs rollback
**Time**: 15-30 minutes
**Risk**: Medium-High

**Note**: This application is **stateless** (no database). If you add a database later, document migration rollback here.

**Placeholder Steps**:
1. Identify migration version
2. Run down migration
3. Rollback application code
4. Verify data integrity

---

### Scenario 3: Partial Rollback (Backend OR Frontend Only)

#### Rollback Backend Only

```bash
cd /path/to/tokenlab-ui-clean-react

# Stop backend
pkill -f "uvicorn"

# Checkout backend files from specific version
git checkout tags/v1.0.0 -- backend/ src/ requirements.txt

# Reinstall
pip install -r requirements.txt

# Restart
cd backend && python -m app.main
```

#### Rollback Frontend Only

```bash
cd /path/to/tokenlab-ui-clean-react

# Checkout frontend files
git checkout tags/v1.0.0 -- frontend/

# Reinstall
cd frontend && npm install

# Rebuild
npm run build

# Deploy build (if static hosting)
# rsync -av dist/ /var/www/html/
```

---

### Scenario 4: Dependency Rollback Only

**Trigger**: New dependency version breaks compatibility
**Time**: 5 minutes
**Risk**: Low

```bash
# Restore requirements.txt from previous version
git checkout tags/v1.0.0 -- requirements.txt

# Uninstall all packages
pip freeze | xargs pip uninstall -y

# Reinstall from rolled-back requirements
pip install -r requirements.txt

# Verify
python -c "import matplotlib; print(matplotlib.__version__)"
```

---

## Rollback Checklist

Use this checklist for any rollback:

### Pre-Rollback
- [ ] Identify target version/tag
- [ ] Verify target version is stable (check test results)
- [ ] Create incident ticket (if not already created)
- [ ] Notify team in #incidents channel
- [ ] Take note of current version (for potential roll-forward)

### During Rollback
- [ ] Stop all running services
- [ ] Backup current logs
- [ ] Checkout target version
- [ ] Reinstall dependencies
- [ ] Restart services
- [ ] Verify health endpoint responds
- [ ] Run smoke tests

### Post-Rollback
- [ ] Verify application functionality
- [ ] Check error logs for issues
- [ ] Monitor for 15 minutes
- [ ] Update status page/incident ticket
- [ ] Document root cause
- [ ] Schedule post-mortem

---

## Version History

| Version | Date | Deployed By | Status | Notes |
|---------|------|-------------|--------|-------|
| v1.0.0 | 2026-01-25 | DevOps | ✅ Stable | Initial production release |
| v0.9.0 | 2026-01-20 | DevOps | ⚠️  Unstable | Monte Carlo bugs |

(Update this table with each deployment)

---

## Rollback Decision Matrix

| Issue Severity | Response Time | Action |
|---------------|---------------|---------|
| P0 (Critical outage) | Immediate | Rollback immediately, investigate later |
| P1 (Major degradation) | < 15 min | Assess if rollback needed, rollback if fix > 30min |
| P2 (Minor issues) | < 1 hour | Attempt hotfix first, rollback if fix risky |
| P3 (Cosmetic) | Next deploy | Do not rollback, fix in next release |

---

## Testing Rollback Procedure

**Recommendation**: Test rollback monthly in staging

```bash
# Staging rollback test
# 1. Deploy latest to staging
# 2. Run this script
# 3. Verify functionality
# 4. Document any issues

cd /path/to/staging/tokenlab-ui-clean-react

# Rollback
git checkout tags/v1.0.0
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Test
pytest tests/
curl http://staging:8000/api/v1/health

# Results:
# ✅ Rollback successful
# ⏱️  Time taken: X minutes
# 📝 Notes: (any issues encountered)
```

---

## Emergency Contacts

**During Rollback Incident**:
- Engineering Lead: [Contact info]
- DevOps On-Call: [Contact info]
- Product Manager: [Contact info]

**Escalation Path**:
1. Engineering Lead (first 15 min)
2. CTO (if not resolved after 30 min)

---

## Common Rollback Issues & Solutions

### Issue 1: "ModuleNotFoundError" after rollback

**Cause**: Cached bytecode from newer version
**Solution**:
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Issue 2: Frontend build fails after rollback

**Cause**: node_modules incompatibility
**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue 3: Port already in use

**Cause**: Old process still running
**Solution**:
```bash
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

### Issue 4: Git checkout fails (uncommitted changes)

**Cause**: Local modifications not committed
**Solution**:
```bash
# Option 1: Stash changes
git stash
git checkout tags/v1.0.0

# Option 2: Force (lose changes)
git checkout -f tags/v1.0.0
```

---

## Rollback Metrics

Track these metrics for each rollback:

- **Time to Detect**: Time from deployment to issue detection
- **Time to Decision**: Time from detection to rollback decision
- **Time to Execute**: Time from decision to rollback complete
- **Total Downtime**: Time from issue start to service restored

**Goal**: Total rollback time < 10 minutes

---

## Future Improvements

### 1. Blue-Green Deployment
- Run old and new versions simultaneously
- Switch traffic with load balancer
- Instant rollback (just switch traffic back)

### 2. Canary Releases
- Deploy to 10% of users first
- Monitor for errors
- Rollback before full deployment if issues

### 3. Automated Rollback
- Monitor error rate
- Auto-rollback if error rate > threshold
- Requires: metrics pipeline + automation script

### 4. Database Migration Versioning
- If database added: use migration tool (e.g., Alembic)
- Version migrations with application code
- Test rollback in staging

---

## Rollback Communication Template

**For team notifications:**

```
🔄 ROLLBACK IN PROGRESS

Version: [current] → [target]
Reason: [brief description]
ETA: [estimated completion time]
Status: [In Progress / Complete]

Details:
- Issue: [what went wrong]
- Impact: [user impact]
- Rollback target: [version]
- Expected completion: [time]

Updates: [link to incident tracker]
```

---

**Document Version**: 1.0
**Effective Date**: 2026-01-26
**Next Review**: After first production rollback
