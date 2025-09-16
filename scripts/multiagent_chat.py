#!/usr/bin/env python3
import os
import sys

# Add the parent directory to the path so we can import triad
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from triad.agents.cli_chat import main

if __name__ == "__main__":
    raise SystemExit(main())
