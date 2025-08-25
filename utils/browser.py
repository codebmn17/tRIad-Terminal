#!/usr/bin/env python3
"""
Browser utilities for Triad Terminal

This module provides a simple interface to open URLs using the system's default browser.
It wraps the existing platform compatibility layer functionality.
"""

import webbrowser
from typing import Optional


def open_url(url: str) -> bool:
    """
    Open URL in default browser
    
    Args:
        url: The URL to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def open_url_new_tab(url: str) -> bool:
    """
    Open URL in a new tab
    
    Args:
        url: The URL to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception:
        return False


def open_url_new_window(url: str) -> bool:
    """
    Open URL in a new window
    
    Args:
        url: The URL to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        webbrowser.open_new(url)
        return True
    except Exception:
        return False