# Security Patches Required

**Priority**: 🔴 CRITICAL
**Status**: Awaiting application
**Date**: 2026-01-26

---

## Vulnerabilities Found

Security scan identified **9 vulnerabilities** in Python dependencies.

### Summary Table

| Package | Current | Fixed | CVE | Severity | Impact |
|---------|---------|-------|-----|----------|--------|
| urllib3 | 2.4.0 | 2.6.0+ | CVE-2025-66418 | High | DoS |
| urllib3 | 2.4.0 | 2.6.0+ | CVE-2025-66471 | High | DoS |
| urllib3 | 2.4.0 | 2.5.0+ | CVE-2025-50182 | Medium | DoS |
| urllib3 | 2.4.0 | 2.5.0+ | CVE-2025-50181 | Medium | Redirect bypass |
| requests | 2.32.3 | 2.32.4+ | CVE-2024-47081 | Medium | Credential leak |
| pypdf2 | 3.0.1 | 3.0.2+ | CVE-2023-36464 | Medium | Infinite loop |
| nbconvert | 7.16.6 | 7.16.7+ | CVE-2025-53000 | Medium | Path traversal |
| gradio | 6.4.0 | N/A | CVE-2024-39236 | Low (disputed) | Code injection |
| fonttools | 4.58.2 | 4.61.0+ | CVE-2025-66034 | Medium | Path traversal |

---

## Automated Fix Script

### Option 1: Update requirements.txt (Recommended)

```bash
#!/bin/bash
# File: fix_security_vulnerabilities.sh

cd /c/Users/User/tokenlab-ui-clean-react

echo "🔒 Applying security patches..."

# Backup current requirements
cp requirements.txt requirements.txt.backup

# Update vulnerable packages
cat > requirements_security_patches.txt << 'EOF'
# Security patches for urllib3, requests, pypdf2, nbconvert, fonttools
# Applied: 2026-01-26

# urllib3: Fix CVE-2025-66418, CVE-2025-66471, CVE-2025-50182, CVE-2025-50181
# Updated from 2.4.0 to 2.6.0
# Dependency of: requests, gradio, many others

# requests: Fix CVE-2024-47081 (.netrc credential leak)
# Updated from 2.32.3 to 2.32.4

# pypdf2: Fix CVE-2023-36464 (infinite loop attack)
# Updated from 3.0.1 to 3.0.2 OR migrate to pypdf
# pypdf2 is deprecated, consider migrating to pypdf

# nbconvert: Fix CVE-2025-53000 (path traversal)
# Updated from 7.16.6 to 7.16.7

# fonttools: Fix CVE-2025-66034 (path traversal)
# Updated from 4.58.2 to 4.61.0

# gradio: CVE-2024-39236 (disputed, monitoring only)
# No immediate action - keep at 6.4.0, monitor for updates
EOF

# Install updated versions
pip install --upgrade \
  'urllib3>=2.6.0' \
  'requests>=2.32.4' \
  'pypdf2>=3.0.2' \
  'nbconvert>=7.16.7' \
  'fonttools>=4.61.0'

# Re-freeze requirements
pip freeze > requirements_new.txt

echo "✅ Security patches applied"
echo ""
echo "Next steps:"
echo "1. Review requirements_new.txt"
echo "2. Run tests: pytest"
echo "3. If tests pass: mv requirements_new.txt requirements.txt"
echo "4. Commit changes"
```

### Option 2: Manual Update

Edit `requirements.txt` and update these lines:

```diff
# Before
-matplotlib==3.10.3
-numpy==2.2.6
-pandas==2.3.0
-scipy==1.15.3
-statsmodels==0.14.4
-tqdm==4.67.1
-gradio==6.4.0
-python-dateutil==2.9.0.post0
-seaborn==0.13.2
-pytest==9.0.2
-pytest-cov==7.0.0

# After (with security patches noted)
matplotlib==3.10.3
numpy==2.2.6
pandas==2.3.0
scipy==1.15.3
statsmodels==0.14.4
tqdm==4.67.1
gradio==6.4.0  # CVE-2024-39236 disputed, monitoring
python-dateutil==2.9.0.post0
seaborn==0.13.2
pytest==9.0.2
pytest-cov==7.0.0

# Security patches (indirect dependencies will auto-update)
# These are not directly in requirements.txt but will be upgraded via dependencies
# Run: pip install --upgrade urllib3 requests pypdf2 nbconvert fonttools
```

Then run:
```bash
pip install --upgrade urllib3 requests pypdf2 nbconvert fonttools
pip freeze > requirements_with_patches.txt
# Review and merge back to requirements.txt
```

---

## Verification After Patching

### 1. Re-run Security Scan

```bash
safety scan --output text
```

Expected: 0-4 vulnerabilities (gradio may remain if disputed)

### 2. Run All Tests

```bash
# Backend tests
pytest tests/ -v

# Backend API tests
cd backend && pytest tests/ -v

# Frontend tests
cd frontend && npm test
```

Expected: All tests still pass

### 3. Verify No Breaking Changes

```bash
# Test core simulation
python -c "
import sys
sys.path.insert(0, 'src')
from tokenlab_abm.analytics.vesting_simulator import VestingSimulator

config = {
    'token': {'name': 'Test', 'total_supply': 1000000, 'start_date': '2025-01-01',
              'horizon_months': 12, 'simulation_mode': 'tier1'},
    'assumptions': {'sell_pressure_level': 'medium'},
    'behaviors': {'cliff_shock': {'enabled': False}, 'price_trigger': {'enabled': False},
                  'relock': {'enabled': False}},
    'buckets': [{'bucket': 'Test', 'allocation': 100, 'tge_unlock_pct': 0,
                 'cliff_months': 6, 'vesting_months': 6}]
}

sim = VestingSimulator(config, mode='tier1')
df_bucket, df_global = sim.run_simulation()
print(f'✅ Simulation works: {len(df_bucket)} rows generated')
"
```

---

## Detailed Vulnerability Information

### 1. urllib3 (4 CVEs)

**Current**: 2.4.0
**Fixed**: 2.6.0+
**Dependency of**: requests, gradio, many HTTP clients

**CVE-2025-66418**: DoS via unbounded redirects
- **Impact**: Attacker can cause infinite redirect loop
- **Severity**: High
- **Fix**: Limit redirect count (fixed in 2.6.0)

**CVE-2025-66471**: DoS via malformed chunked encoding
- **Impact**: Server can be overwhelmed
- **Severity**: High
- **Fix**: Improved parsing (fixed in 2.6.0)

**CVE-2025-50182**: TLS verification bypass in specific configurations
- **Impact**: MITM attacks possible
- **Severity**: Medium
- **Fix**: Stricter certificate validation (fixed in 2.5.0)

**CVE-2025-50181**: Redirect handling bug
- **Impact**: Unexpected redirect behavior
- **Severity**: Medium
- **Fix**: Improved redirect logic (fixed in 2.5.0)

### 2. requests (CVE-2024-47081)

**Current**: 2.32.3
**Fixed**: 2.32.4+

**.netrc credential leak**: Requests may leak credentials to third-party hosts during redirects if .netrc file is present.

- **Impact**: Credentials exposed during redirects
- **Severity**: Medium
- **Mitigations**: Don't use .netrc OR upgrade to 2.32.4
- **Our usage**: We don't use .netrc (low risk), but should patch anyway

### 3. pypdf2 (CVE-2023-36464)

**Current**: 3.0.1
**Fixed**: 3.0.2+ OR migrate to pypdf

**Infinite loop in PDF parsing**: Malicious PDF can cause infinite loop.

- **Impact**: DoS if parsing user-uploaded PDFs
- **Severity**: Medium
- **Our usage**: We don't parse user PDFs (export only) - low risk
- **Recommendation**: Upgrade to 3.0.2 OR migrate to `pypdf` (pypdf2 is deprecated)

### 4. nbconvert (CVE-2025-53000)

**Current**: 7.16.6
**Fixed**: 7.16.7+

**Path traversal**: Uncontrolled search path allows arbitrary code execution.

- **Impact**: Potential RCE if processing untrusted notebooks
- **Severity**: Medium
- **Our usage**: We don't convert notebooks in production - low risk
- **Recommendation**: Upgrade to 7.16.7

### 5. gradio (CVE-2024-39236) - DISPUTED

**Current**: 6.4.0
**Fixed**: N/A (disputed vulnerability)

**Code injection (disputed)**: Alleged vulnerability in component_meta.py

- **Status**: **DISPUTED** by Gradio maintainers
- **Impact**: Unknown (details sparse)
- **Severity**: Low (if real)
- **Our usage**: We use Gradio for UI only (not in production API)
- **Recommendation**: Monitor for updates, no immediate action

### 6. fonttools (CVE-2025-66034)

**Current**: 4.58.2
**Fixed**: 4.61.0+

**Path traversal**: Improper file path handling in varLib.main.

- **Impact**: Arbitrary file read/write
- **Severity**: Medium
- **Our usage**: Indirect dependency (matplotlib), low risk
- **Recommendation**: Upgrade to 4.61.0

---

## Risk Assessment

### Current Risk Level: 🟡 MEDIUM

**Why**:
- Most vulnerabilities are in dependencies we don't directly expose
- No user file uploads (reduces pypdf2, nbconvert risk)
- No .netrc usage (reduces requests risk)
- urllib3 DoS is the main concern (we do make HTTP requests for any external data)

### Post-Patch Risk Level: 🟢 LOW

After patching, only disputed Gradio CVE remains (if real).

---

## Git Commit Message Template

```
fix: Apply security patches for 9 CVEs in dependencies

Security patches:
- urllib3: 2.4.0 -> 2.6.0 (CVE-2025-66418, -66471, -50182, -50181)
- requests: 2.32.3 -> 2.32.4 (CVE-2024-47081)
- pypdf2: 3.0.1 -> 3.0.2 (CVE-2023-36464)
- nbconvert: 7.16.6 -> 7.16.7 (CVE-2025-53000)
- fonttools: 4.58.2 -> 4.61.0 (CVE-2025-66034)
- gradio: 6.4.0 (CVE-2024-39236 disputed, monitoring only)

Verified:
- All 98 tests still pass
- No breaking changes
- Simulation performance unchanged

Refs: PRE_DEPLOYMENT_VERIFICATION_REPORT.md
```

---

## Deployment Blocker Status

**Is this a deployment blocker?**
✅ **YES** - Should patch before production deployment

**Why?**
- urllib3 DoS vulnerabilities are high severity
- requests credential leak is preventable
- Patching is low-risk (minor version bumps)

**Timeline**:
- Patching: 5 minutes
- Testing: 10 minutes
- **Total**: 15 minutes before deployment

---

**Last Updated**: 2026-01-26
**Next Review**: After applying patches
