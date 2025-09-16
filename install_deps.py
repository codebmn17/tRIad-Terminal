# Double-click this to install required packages (no command line needed).
import os
import subprocess
import sys

PY_CMD = sys.executable

def run(cmd):
    print(f"> {cmd}")
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed (ignored): {e}")

def main():
    print("Upgrading pip...")
    run(f'"{PY_CMD}" -m pip install --upgrade pip')

    req = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req):
        print("Installing from requirements.txt ...")
        run(f'"{PY_CMD}" -m pip install -r "{req}"')
    else:
        print("requirements.txt not found, installing core packages directly...")
        pkgs = [
            "fastapi", "uvicorn[standard]",
            "scikit-learn", "numpy",
            "pyttsx3", "playsound==1.2.2", "gTTS",
            "SpeechRecognition"
        ]
        run(f'"{PY_CMD}" -m pip install ' + " ".join(pkgs))

    # Try to install PyAudio (optional). May fail on some systems.
    print("Attempting to install PyAudio (optional for microphone input)...")
    run(f'"{PY_CMD}" -m pip install pyaudio')

    print("\nAll done. If any step failed, you can still run TTS and the API.")
    print("Next, double-click start_api.py to launch the learning API.")
    input("\nPress Enter to close this window...")

if __name__ == "__main__":
    main()
