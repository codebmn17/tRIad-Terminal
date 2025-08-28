#!/usr/bin/env python3
"""
Backward compatibility shim for assistant-ML.py

This file has been renamed to assistant_ml.py to follow Python naming conventions.
Please update your imports to use 'assistant_ml' instead of 'assistant-ML'.
"""

raise ImportError(
    "The file 'assistant-ML.py' has been renamed to 'assistant_ml.py' to follow Python naming conventions. "
    "Please update your import to: 'from agents.learning.assistant_ml import ...' "
    "instead of 'from agents.learning.assistant-ML import ...'"
)