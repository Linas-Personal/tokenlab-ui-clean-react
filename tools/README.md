# Verification Tools

This directory contains **fixed** verification scripts based on ChatGPT's comprehensive feedback. These tools address critical issues in the original verification instructions.

## 🔧 What Was Fixed

### 1. **Path Expansion Issues** ✅
- **Problem**: Using `~` in Python strings doesn't auto-expand
- **Fix**: All scripts now use `Path(...).expanduser().resolve()`

### 2. **Import Caching Issues** ✅
- **Problem**: Original parity test imported the same module twice
- **Fix**: Subprocess-based approach runs each simulator in separate process
- **Script**: `compare_parity_subprocess.py`

### 3. **Regex Issues in grep** ✅
- **Problem**: Using `\|` without `-E` flag treats it as literal
- **Fix**: All bash scripts now use `grep -E` for extended regex
- **Script**: `analyze_backend_api.sh`

### 4. **Method Inspection Issues** ✅
- **Problem**: `inspect.ismethod` doesn't work on class definitions
- **Fix**: Use `inspect.isfunction` for classes
- **Scripts**: `document_backend_interface.py`, `extract_method_signatures.py`

### 5. **Contract-Driven Testing** ✅
- **Improvement**: Replace grep-based verification with schema validation
- **Scripts**: `test_contracts.py` + contract files in `../contracts/`

## 📁 File Structure

```
tools/
├── README.md                       # This file
├── run_vesting_sim.py             # Canonical JSON runner (copy to both repos)
├── compare_parity_subprocess.py   # Subprocess-based parity testing
├── extract_method_signatures.py   # AST-based method extraction
├── document_backend_interface.py  # Backend API documentation
├── test_edge_cases.py             # Edge case testing
├── test_contracts.py              # Contract-driven integration tests
└── analyze_backend_api.sh         # Bash script for API analysis

contracts/
├── requests/
│   ├── tier1_basic.json           # Tier 1 test config
│   └── tier2_staking.json         # Tier 2 test config
└── responses/
    └── expected_schema.json       # Expected output schema
```

## 🚀 Quick Start

### 1. Parity Testing (Subprocess Method)

**Purpose**: Compare your implementation with original TokenLab

**Setup**:
```bash
# 1. Clone original TokenLab (if not already done)
cd ~
git clone https://github.com/stelios12312312/TokenLab.git

# 2. Copy the runner script to original repo
cp ~/tokenlab-ui-clean-react/tools/run_vesting_sim.py ~/TokenLab/tools/

# 3. Update paths in compare_parity_subprocess.py if needed
```

**Run**:
```bash
python tools/compare_parity_subprocess.py
```

**What it does**:
- Creates a test config
- Runs your simulator in isolated process
- Runs original TokenLab in isolated process (if available)
- Compares JSON outputs with tolerance

**Why this approach works**:
- No module caching issues
- Each simulator uses its own PYTHONPATH
- Works even if both have same module names
- Produces diffable artifacts (`out_ui.json`, `out_orig.json`)

### 2. Method Signature Comparison

**Purpose**: Document differences in class methods

**Run**:
```bash
python tools/extract_method_signatures.py
```

**Output**:
- Prints comparison to console
- Saves to `~/method_comparison.json`

**Shows**:
- New methods (only in your implementation)
- Missing methods (only in original)
- Signature changes (different parameters)

### 3. Backend API Documentation

**Purpose**: Document what the backend exposes

**Run**:
```bash
python tools/document_backend_interface.py
```

**Shows**:
- VestingSimulator methods with signatures
- Gradio app functions
- Data structure classes

### 4. Edge Case Testing

**Purpose**: Find bugs in input handling

**Run**:
```bash
python tools/test_edge_cases.py
```

**Tests**:
- Zero allocations
- 100% TGE unlock
- Invalid dates
- Negative values
- Allocation sum ≠ 100%
- Very long vesting periods

### 5. Contract-Driven Integration Testing

**Purpose**: Validate backend-frontend integration via schemas

**Run**:
```bash
python tools/test_contracts.py
```

**How it works**:
1. Loads configs from `contracts/requests/*.json`
2. Runs simulator for each config
3. Validates output against `contracts/responses/expected_schema.json`
4. Reports schema violations

**Add more tests**:
```bash
# Create new request config
cat > contracts/requests/tier3_monte_carlo.json << 'EOF'
{
  "token_name": "MonteCarloToken",
  "tier": 3,
  "monte_carlo_iterations": 100,
  ...
}
EOF

# Re-run
python tools/test_contracts.py
```

### 6. Backend API Analysis (Bash)

**Purpose**: Find all API entry points

**Run**:
```bash
bash tools/analyze_backend_api.sh
```

**Outputs**:
- `backend_api_surface.txt` - All run/simulate/calculate methods
- `backend_data_structures.txt` - All Config/Result classes

## 🎯 Recommended Workflow

### For Initial Verification

```bash
# 1. Document your implementation
python tools/document_backend_interface.py

# 2. Test edge cases
python tools/test_edge_cases.py

# 3. Run contract tests
python tools/test_contracts.py

# 4. Compare with original (if available)
python tools/compare_parity_subprocess.py

# 5. Extract method differences
python tools/extract_method_signatures.py

# 6. Analyze backend API
bash tools/analyze_backend_api.sh
```

### For Continuous Testing (CI/CD)

```bash
# Add to .github/workflows/test.yml or similar:
- name: Edge case tests
  run: python tools/test_edge_cases.py

- name: Contract tests
  run: python tools/test_contracts.py

- name: Parity tests
  run: python tools/compare_parity_subprocess.py
  continue-on-error: true  # Original may not be available
```

## 🐛 Troubleshooting

### "Module not found" errors

```bash
# Verify PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"

# Run from project root
cd ~/tokenlab-ui-clean-react
python tools/test_edge_cases.py
```

### Parity test always passes (false positive)

**Diagnosis**: You're using the old import method (both imports resolve to same module)

**Solution**: Use `compare_parity_subprocess.py` instead

### grep commands return nothing

**Diagnosis**: Missing `-E` flag or wrong directory

**Solution**: Use `analyze_backend_api.sh` or add `-E` flag:
```bash
grep -R -n -E 'pattern' directory --include="*.py"
```

### Original TokenLab comparison fails

**Expected**: Your implementation may have intentional differences

**Action**:
1. Check if differences are intentional (new features, bug fixes)
2. Document mapping between implementations
3. Update README to note: "Inspired by TokenLab, not 1:1 port"

## 📊 Understanding Test Results

### Parity Test

**✅ PASS**: Outputs match within tolerance
- Implementations are equivalent

**❌ FAIL**: Outputs differ
- Could be:
  - Different algorithms
  - Different defaults
  - Bug in one implementation
  - Intentional enhancement

**Action**: Review diff between `out_ui.json` and `out_orig.json`

### Contract Test

**✅ PASS**: Output matches schema
- Backend returns expected structure
- Frontend can safely consume

**❌ FAIL**: Schema violation
- Missing required fields
- Wrong data types
- Unexpected structure

**Action**: Update schema or fix backend output

### Edge Case Test

**✅ PASS**: No error raised
- Input handling is robust

**❌ FAIL**: Exception raised
- May need input validation
- May need better error messages

**Action**: Add validation or document assumptions

## 🔬 Advanced Usage

### Custom Test Configs

Create custom configs for your specific scenarios:

```python
# contracts/requests/custom_scenario.json
{
  "token_name": "CustomToken",
  "total_supply": 500000000,
  "tier": 2,
  "buckets": [
    {
      "name": "Strategic",
      "allocation_pct": 15.0,
      "tge_unlock_pct": 5.0,
      "cliff_months": 3,
      "vesting_months": 18
    }
  ],
  "staking": {
    "enabled": true,
    "apy": 20.0
  }
}
```

### Golden Master Testing

Save known-good outputs for regression testing:

```bash
# 1. Generate golden output
python tools/run_vesting_sim.py \
  --config contracts/requests/tier1_basic.json \
  --out contracts/responses/tier1_basic_golden.json

# 2. Later, compare new run against golden
python tools/run_vesting_sim.py \
  --config contracts/requests/tier1_basic.json \
  --out /tmp/tier1_new.json

diff contracts/responses/tier1_basic_golden.json /tmp/tier1_new.json
```

### Performance Profiling

```python
# Add to test_edge_cases.py or create new script
import time
import memory_profiler

@memory_profiler.profile
def profile_tier3():
    config = {
        "tier": 3,
        "monte_carlo_iterations": 1000,
        # ... rest of config
    }

    start = time.time()
    sim = VestingSimulator(config)
    result = sim.run()
    duration = time.time() - start

    print(f"⏱️  Duration: {duration:.2f}s")
    return result
```

## 📝 Key Takeaways from ChatGPT Feedback

1. **Reality Check**: The two repos aren't the same
   - Your implementation: Vesting Simulator UI
   - Original TokenLab: General ABM framework
   - Parity may not be appropriate/possible

2. **Verification Goals**:
   - ✅ Backend ↔ Frontend integration works
   - ✅ Outputs are mathematically correct
   - ✅ Edge cases handled gracefully
   - ⚠️ Parity with original (only if applicable)

3. **Focus Areas**:
   - Contract-driven testing (schema validation)
   - Edge case robustness
   - Performance benchmarks
   - Documentation accuracy

## 🆘 Getting Help

If tests fail or you find issues:

1. Check the output files in `~` directory:
   - `parity_config.json`
   - `out_ui.json`
   - `out_orig.json`
   - `method_comparison.json`

2. Review test output carefully - errors often indicate:
   - Missing input validation
   - Undocumented assumptions
   - Integration mismatches

3. Update schemas in `contracts/responses/` to reflect reality

4. Document any intentional differences from original TokenLab

## 🎓 Reference

- Original instructions: See root directory verification docs
- ChatGPT feedback: Addressed critical import caching, path expansion, and grep issues
- This implementation: Robust, process-isolated, contract-driven approach

---

**Last Updated**: 2026-01-26
**Status**: All critical issues from ChatGPT feedback addressed ✅
