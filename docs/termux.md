# Termux (Android) Setup

This project includes a Termux-friendly dependency set and helper scripts to run on Android without Rust builds.

## System packages

```sh
pkg update -y
pkg install -y python git clang make pkg-config openssl libffi
```

## Python dependencies

```sh
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-termux.txt
```

Or run the installer script:

```sh
chmod +x scripts/install_termux.sh
./scripts/install_termux.sh
```

## Run the API

A convenience runner is included and will auto-detect the app entrypoint (`api.app:app`, then `app:app`, then `api.main:app`):

```sh
chmod +x scripts/run_termux.sh
./scripts/run_termux.sh
```

If you prefer to run manually:

- If your entrypoint is `api/app.py` with `app`:
  ```sh
  export PYTHONPATH=$PWD
  python -m uvicorn api.app:app --host 0.0.0.0 --port 8158
  ```
- If your entrypoint is `app.py` with `app`:
  ```sh
  export PYTHONPATH=$PWD
  python -m uvicorn app:app --host 0.0.0.0 --port 8158
  ```
- If your entrypoint is `api/main.py` with `app`:
  ```sh
  export PYTHONPATH=$PWD
  python -m uvicorn api.main:app --host 0.0.0.0 --port 8158
  ```

## Quick health check

```sh
curl -s http://127.0.0.1:8158/health
```

## Notes

- Avoid `uvicorn[standard]` (pulls `watchfiles`, which requires Rust).
- Avoid Pydantic v2 on Termux (pulls `pydantic-core`, which is Rust).
- `--reload` can work with a polling reloader if `watchfiles` is not installed.
- The CI workflow validates Termux-safe pins by installing `requirements-termux.txt` and importing the app.
