#!/usr/bin/env python3
"""
Run the production-ready tRIad Terminal API.

This script starts the FastAPI application using Uvicorn with production settings.
"""

import os
import sys

import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def main():
    """Main entry point for the API server."""
    print("🚀 Starting tRIad Terminal API...")
    print("📍 API will be available at: http://127.0.0.1:8000")
    print("📖 API documentation at: http://127.0.0.1:8000/docs")
    print("🔄 Interactive docs at: http://127.0.0.1:8000/redoc")
    print("\n💡 Press Ctrl+C to stop the server")
    print("-" * 50)

    try:
        uvicorn.run(
            "api.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
