# Double-click this file to start the API on http://127.0.0.1:8000
import uvicorn

if __name__ == "__main__":
    print("Starting Triad Learning API at http://127.0.0.1:8000 ...")
    print("Leave this window open. Open tests/api_tester.html in your browser to try it.")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
