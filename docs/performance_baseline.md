# Performance Baseline Documentation

This document provides instructions for gathering performance baseline metrics for Triad Terminal. Use these measurements to track performance improvements and identify regressions over time.

## Quick Setup (5 minutes)

1. **Enable performance logging:**
   ```bash
   export TRIAD_PERF=1
   ```

2. **Run the terminal with timing:**
   ```bash
   time python -m triad_terminal --help
   # OR for main entry points:
   time python triad-terminal.py --help
   time python integrated_terminal_Version2.py --help
   ```

3. **Test the performance command:**
   ```bash
   # Start terminal and run:
   /perf
   # OR
   perf
   ```

## Comprehensive Baseline (15 minutes)

### 1. Startup Time Measurement

Measure cold startup time of different terminal variants:

```bash
# Measure main terminal startup
time python triad-terminal.py --help
time python secure_terminal_Version2.py --help
time python integrated_terminal_Version2.py --help

# Measure with different flags
time python triad-terminal.py --debug --help
time python secure_terminal_Version2.py --dev --help
```

**Record in table below.**

### 2. Import Time Analysis

Measure import costs of key modules:

```bash
# Basic Python import timing
python -X importtime -c "import triad_terminal" 2>&1 | tail -10

# Specific module imports
python -c "import time; start=time.time(); import triad_terminal.perf_utils; print(f'perf_utils: {(time.time()-start)*1000:.2f}ms')"
python -c "import time; start=time.time(); import triad_terminal.perf_runtime; print(f'perf_runtime: {(time.time()-start)*1000:.2f}ms')"
```

### 3. Memory Usage Baseline

```bash
# Memory usage during startup
/usr/bin/time -v python triad-terminal.py --help 2>&1 | grep "Maximum resident set size"

# Memory usage during operation (requires terminal session)
ps aux | grep "python.*triad" | grep -v grep
```

### 4. Performance Profiling with py-spy (Optional)

If py-spy is available:

```bash
# Install py-spy (optional)
pip install py-spy

# Profile startup
py-spy record -o startup_profile.svg -d 10 -- python triad-terminal.py

# Profile during operation (run in another terminal)
py-spy top -p <triad_terminal_pid>
```

### 5. Command Latency Testing

Test common command response times:

```bash
# Enable performance logging
export TRIAD_PERF=1

# Start terminal and run commands, observe timing logs:
help
status
clear
/perf
exit
```

## Baseline Measurement Table

Fill in your measurements:

| Metric | Measurement | Date | Environment |
|--------|-------------|------|-------------|
| **Startup Times** |
| triad-terminal.py --help | _____ ms | _______ | _______ |
| secure_terminal_Version2.py --help | _____ ms | _______ | _______ |
| integrated_terminal_Version2.py --help | _____ ms | _______ | _______ |
| triad-terminal.py --debug --help | _____ ms | _______ | _______ |
| **Import Times** |
| triad_terminal package | _____ ms | _______ | _______ |
| triad_terminal.perf_utils | _____ ms | _______ | _______ |
| triad_terminal.perf_runtime | _____ ms | _______ | _______ |
| **Memory Usage** |
| Peak memory during startup | _____ MB | _______ | _______ |
| Steady-state memory | _____ MB | _______ | _______ |
| **Command Latencies** |
| help command | _____ ms | _______ | _______ |
| status command | _____ ms | _______ | _______ |
| /perf command | _____ ms | _______ | _______ |

## Environment Information Template

Record your environment details:

```
Date: ___________
Python Version: ___________
OS: ___________
CPU: ___________
RAM: ___________
Storage: ___________
Terminal: ___________
Shell: ___________
```

## Performance Hotspots to Monitor

Common areas that may impact performance:

1. **Terminal startup sequence**
   - Module imports
   - Configuration loading
   - Security system initialization
   - UI system setup

2. **Command processing**
   - Command parsing
   - Security checks
   - Plugin loading
   - Response generation

3. **Background operations**
   - Voice assistant processing
   - AI integration overhead
   - Monitoring/logging systems

## Automation Scripts

Create these helper scripts for repeated measurements:

### measure_startup.sh
```bash
#!/bin/bash
echo "Measuring Triad Terminal startup times..."
for i in {1..5}; do
    echo "Run $i:"
    time python triad-terminal.py --help 2>&1 | grep real
done
```

### measure_imports.py
```python
#!/usr/bin/env python3
import time
import sys

modules = [
    "triad_terminal",
    "triad_terminal.perf_utils",
    "triad_terminal.perf_runtime",
    "triad_terminal.commands.perf"
]

for module in modules:
    start = time.time()
    try:
        __import__(module)
        duration = (time.time() - start) * 1000
        print(f"{module}: {duration:.2f}ms")
    except ImportError as e:
        print(f"{module}: FAILED - {e}")
```

## Next Steps

After gathering baseline measurements:

1. **Commit your measurements** to version control in this file
2. **Set up monitoring** for regressions in CI/CD
3. **Identify optimization targets** from the measurements
4. **Re-measure after changes** to track improvements

## Notes

- Run measurements multiple times and average for accuracy
- Measure on the same system/environment for consistency
- Consider both cold start and warm start scenarios
- Document any significant environmental factors
