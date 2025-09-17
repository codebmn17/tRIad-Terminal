"""
Browser utilities for Triad Terminal
Provides safe URL opening functionality
"""

import sys
import webbrowser


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
 copilot/fix-1f51a615-a20d-476a-b14f-a5ee1cba80a2
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'https://' + url

        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
main

        return webbrowser.open(url, new=new, autoraise=autoraise)
    except Exception:
        return False


def get_default_browser() -> str | None:
    """Get the name of the default browser."""
    try:
        browser = webbrowser.get()
        return browser.name if hasattr(browser, "name") else str(type(browser).__name__)
    except Exception:
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils/browser.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    open_url(url)
