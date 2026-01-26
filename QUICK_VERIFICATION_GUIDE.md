# Quick Verification Guide

**TL;DR**: Run `python tools/run_all_verifications.py` to verify everything.

## 🚀 One-Command Verification

```bash
cd ~/tokenlab-ui-clean-react
python tools/run_all_verifications.py
```

This runs all verification scripts in the correct order.

## 🎯 Individual Tests

### 1. Test Edge Cases (2 minutes)

```bash
python tools/test_edge_cases.py
```

**What it does**: Tests 8+ edge cases (zero allocation, invalid dates, etc.)
**Expected**: Some may fail (reveals validation gaps)
**Action**: Fix bugs or add input validation

### 2. Contract Testing (1 minute)

```bash
python tools/test_contracts.py
```

**What it does**: Validates backend outputs match expected schema
**Expected**: Should pass
**Action**: Update schema if outputs changed intentionally

### 3. Document Backend (30 seconds)

```bash
python tools/document_backend_interface.py
```

**What it does**: Lists all backend methods and signatures
**Expected**: Always succeeds
**Action**: Review for completeness

### 4. Compare with Original (optional, 3 minutes)

```bash
# Only if you've cloned original TokenLab
python tools/compare_parity_subprocess.py
```

**What it does**: Compares your implementation with original
**Expected**: May differ (expected if you added features)
**Action**: Document differences as features

### 5. Analyze Backend API (30 seconds)

```bash
bash tools/analyze_backend_api.sh
```

**What it does**: Greps for all API methods
**Expected**: Produces two text files
**Action**: Review for frontend integration

### 6. Extract Method Signatures (1 minute)

```bash
python tools/extract_method_signatures.py
```

**What it does**: Compares method signatures with original
**Expected**: May differ or skip if original not available
**Action**: Document intentional differences

## 📊 Understanding Results

### ✅ Good Results

- **Edge cases pass**: Input validation is robust
- **Contracts pass**: Backend-frontend integration works
- **Parity matches**: Implementation is faithful to original

### ⚠️ Warning Results

- **Some edge cases fail**: Normal - add validation or document assumptions
- **Parity differs**: May be intentional improvements
- **Original repo missing**: Expected if not cloned

### ❌ Action Required

- **All edge cases fail**: Likely a setup issue
- **Contracts fail**: Backend output changed - update schema or fix code
- **Documentation fails**: Import errors - check PYTHONPATH

## 🔧 Setup (One-Time)

### Minimal Setup (Just Your Repo)

```bash
cd ~/tokenlab-ui-clean-react
# Already done - tools are in place!
```

### Full Setup (With Original Comparison)

```bash
# 1. Clone original TokenLab
cd ~
git clone https://github.com/stelios12312312/TokenLab.git

# 2. Copy runner script
cp ~/tokenlab-ui-clean-react/tools/run_vesting_sim.py ~/TokenLab/tools/
```

## 🐛 Common Issues

### "Module not found"

```bash
# Solution: Run from project root
cd ~/tokenlab-ui-clean-react
python tools/test_edge_cases.py
```

### "File not found" (path issues)

✅ Already fixed! All scripts use `Path().expanduser()`

### Parity test always passes

✅ Already fixed! Now uses subprocess isolation

### grep returns nothing

✅ Already fixed! Now uses `grep -E`

## 📁 Output Files

After running verifications, check these files in your home directory:

```bash
ls ~/parity_config.json           # Test configuration
ls ~/out_ui.json                  # Your implementation output
ls ~/out_orig.json                # Original implementation output (if available)
ls ~/method_comparison.json       # Method signature comparison
ls ~/backend_api_surface.txt      # All API methods
ls ~/backend_data_structures.txt  # All data classes
```

## 📝 Quick Checklist

Before deploying or releasing:

- [ ] Edge case tests pass (or failures documented)
- [ ] Contract tests pass
- [ ] Backend documented
- [ ] Frontend integration verified
- [ ] Known differences from original documented (if applicable)

## 🎓 Learn More

- **Detailed guide**: `tools/README.md`
- **What was fixed**: `VERIFICATION_FIXES_APPLIED.md`
- **Original feedback**: Based on ChatGPT's comprehensive analysis

---

**Last Updated**: 2026-01-26
**Time to run all tests**: ~5-10 minutes
**Difficulty**: Easy (just run scripts)
