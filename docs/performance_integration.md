# Performance Monitoring Integration Guide

This guide shows how to integrate the Triad Terminal performance monitoring utilities with existing terminal implementations.

## Quick Integration

### 1. Add Performance Logging to Functions

Wrap existing functions with the `@timed` decorator:

```python
from triad_terminal.perf_utils import timed

# Existing function
@timed
def load_configuration():
    # existing code
    return config

# With custom name
@timed(name="auth_check")
def authenticate_user(username):
    # existing code
    return result
```

### 2. Add Manual Timing Blocks

Use `time_block` context manager for timing code sections:

```python
from triad_terminal.perf_utils import time_block

def process_command(cmd):
    with time_block("command_parsing"):
        parsed = parse_command(cmd)

    with time_block("command_execution"):
        result = execute_command(parsed)

    return result
```

### 3. Track Command Statistics

Record commands for usage analytics:

```python
from triad_terminal.perf_runtime import record_command

def handle_user_input(command):
    record_command(command)  # Track for statistics
    return process_command(command)
```

### 4. Add /perf Command

#### Option A: Direct Integration
```python
from triad_terminal.commands.perf import run as perf_command

def dispatch_command(cmd):
    if cmd == "perf" or cmd == "/perf":
        return perf_command()
    # ... other commands
```

#### Option B: Add to Command List
```python
def get_available_commands():
    commands = [
        {"name": "help", "description": "Show help"},
        {"name": "perf", "description": "Show performance summary"},
        # ... other commands
    ]
    return commands

def process_command(cmd):
    if cmd == "perf":
        from triad_terminal.commands.perf import run
        return run()
    # ... handle other commands
```

## Integration Examples by Terminal Type

### For `integrated_terminal_Version2.py`

Add to the `_process_command` method:

```python
def _process_command(self, cmd: str) -> None:
    """Process a terminal command"""
    from triad_terminal.perf_runtime import record_command

    # Record command for statistics
    record_command(cmd)

    cmd_lower = cmd.lower()

    if cmd_lower == "perf":
        from triad_terminal.commands.perf import run
        result = run()
        self.ui.print_message(result, "info")

    elif cmd_lower == "help":
        # Add timing to existing help
        from triad_terminal.perf_utils import time_block
        with time_block("help_generation"):
            self._show_help()

    # ... rest of existing command handling
```

Add to the available commands:

```python
def _get_available_commands(self) -> List[Dict[str, str]]:
    """Get available commands for the current user"""
    commands = [
        {"name": "help", "description": "Show available commands"},
        {"name": "perf", "description": "Show performance summary"},
        # ... existing commands
    ]
    return commands
```

### For `secure_terminal_Version2.py`

Similar integration in the command handling methods.

### For Custom Terminal Implementations

1. **Import the utilities at the top:**
   ```python
   from triad_terminal.perf_utils import timed, time_block
   from triad_terminal.perf_runtime import record_command
   from triad_terminal.commands.perf import run as perf_command
   ```

2. **Wrap initialization functions:**
   ```python
   @timed(name="terminal_startup")
   def initialize_terminal(self):
       # existing initialization code
   ```

3. **Add command tracking:**
   ```python
   def main_loop(self):
       while running:
           cmd = input("prompt> ")
           record_command(cmd)
           self.process_command(cmd)
   ```

4. **Add performance command:**
   ```python
   def process_command(self, cmd):
       if cmd.lower() in ["perf", "/perf", ":perf"]:
           print(perf_command())
           return
       # ... existing command handling
   ```

## Environment Variable Setup

Users can enable performance logging by setting:

```bash
export TRIAD_PERF=1
```

Or programmatically:

```python
import os
os.environ["TRIAD_PERF"] = "1"
```

## Avoiding Import Cycles

The performance utilities are designed to have minimal dependencies:

- `perf_utils.py`: Only standard library imports
- `perf_runtime.py`: Only standard library imports
- `commands/perf.py`: Only imports from sibling modules

Safe to import from any application module without cycles.

## Performance Impact

- **Without TRIAD_PERF**: Minimal overhead, logging at DEBUG level
- **With TRIAD_PERF**: Logging enabled at INFO level
- **Decorators**: ~1-2µs overhead per function call
- **Context managers**: ~1µs overhead per block
- **Command recording**: ~0.1µs overhead per command

## Testing Integration

Test your integration:

```bash
# Enable performance logging
export TRIAD_PERF=1

# Run your terminal
python your_terminal.py

# In terminal, test:
perf
help
status
perf  # Should show increased command count
```

## Common Integration Patterns

### Pattern 1: Startup Sequence Timing
```python
@timed(name="config_load")
def load_config(self):
    # existing code

@timed(name="security_init")
def init_security(self):
    # existing code

def startup(self):
    with time_block("full_startup"):
        self.load_config()
        self.init_security()
        # other startup tasks
```

### Pattern 2: Command Pipeline Timing
```python
def execute_command(self, cmd):
    record_command(cmd)

    with time_block("command_parse"):
        parsed = self.parse_command(cmd)

    with time_block("command_validate"):
        self.validate_command(parsed)

    with time_block("command_execute"):
        return self.run_command(parsed)
```

### Pattern 3: Conditional Performance Monitoring
```python
import os
from triad_terminal.perf_utils import timed

# Only apply timing in development/debug mode
if os.environ.get("TRIAD_PERF") or os.environ.get("DEBUG"):
    @timed
    def expensive_operation(self):
        # existing code
else:
    def expensive_operation(self):
        # existing code without timing
```

## Next Steps

After integration:

1. **Gather baselines** using `docs/performance_baseline.md`
2. **Set up monitoring** in CI/CD for regressions
3. **Identify bottlenecks** from timing logs
4. **Optimize** based on measurements
