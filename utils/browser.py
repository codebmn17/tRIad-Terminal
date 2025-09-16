"""
Browser utilities for Triad Terminal
Provides safe URL opening functionality
"""

import webbrowser
import sys
import os
from typing import Optional


def open_url(url: str, new: int = 2, autoraise: bool = True) -> bool:
    """
    Open a URL in the default browser.
    
    Args:
        url: The URL to open
        new: 0=same window, 1=new window, 2=new tab
        autoraise: Whether to raise the browser window
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Basic validation
        if not url or not isinstance(url, str):
            return False
            
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'https://' + url
            
        return webbrowser.open(url, new=new, autoraise=autoraise)
    except Exception:
        return False


def get_default_browser() -> Optional[str]:
    """Get the name of the default browser."""
    try:
        browser = webbrowser.get()
        return browser.name if hasattr(browser, 'name') else str(type(browser).__name__)
    except Exception:
        return None

def open_url(url):
    try:
        webbrowser.open(url)
        print(f"Opened {url} in your browser.")
    except Exception as e:
        print(f"Error opening URL: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils/browser.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    open_url(url)
