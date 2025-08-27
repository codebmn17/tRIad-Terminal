import webbrowser
import sys

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
