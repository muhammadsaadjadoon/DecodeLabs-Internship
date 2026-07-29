# Prismora — Multimodal Image Generation Studio

Prismora is an AI-powered image generation workspace built with FastAPI, Gemini, and Cloudflare Workers AI FLUX.1 Schnell. The repository contains one active backend implementation and a static premium frontend served by the same FastAPI application.

## Features

- Natural-language text-to-image generation.
- Gemini-powered prompt enhancement.
- Cloudflare Workers AI FLUX.1 Schnell integration.
- Multiple aspect ratios, visual modes, style directions, image counts, and optional seeds.
- User registration, login, profile, settings, sessions, history, threads, favorites, and image refinement.
- Input moderation and professional safety errors.
- Split network timeouts, retries, exponential backoff, and jitter.
- Memory-conscious response streaming and Base64 extraction.
- Pixel-level image decoding, checksums, dimension validation, and normalization.
- Automated output-safety and visual-quality review.
- SQLite persistence and local image storage.

## Repository structure

```text
prismora-ai-image-studio/
├── .github/workflows/tests.yml
├── backend/
│   ├── static/
│   ├── storage/
│   │   ├── avatars/.gitkeep
│   │   ├── images/.gitkeep
│   │   ├── logs/.gitkeep
│   │   └── tmp/.gitkeep
│   ├── tests/
│   ├── main.py
│   ├── quality_pipeline.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pytest.ini
├── docs/
├── scripts/
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── SECURITY.md
```

## Local setup

### Windows PowerShell

```powershell
.\scripts\setup_windows.ps1
notepad .env
.\scripts\run_windows.ps1
```

### Windows Command Prompt

```bat
scripts\setup_windows.bat
notepad .env
scripts\run_windows.bat
```

### Linux or macOS

```bash
./scripts/setup_unix.sh
nano .env
./scripts/run_unix.sh
```

Open `http://127.0.0.1:8000` after the server starts.

## Environment configuration

Copy `.env.example` to `.env`, then provide your own credentials:

```env
APP_SECRET_KEY=replace_with_a_long_random_secret
GEMINI_API_KEY=your_gemini_api_key
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
```

The root `.env` file is loaded by the backend but ignored by Git.

## Run tests

```bash
cd backend
python -m pip install -r requirements-dev.txt
pytest -q
```

GitHub Actions runs the active test suite automatically on pushes and pull requests.

## Runtime data

The application creates its SQLite database and user-generated files under `backend/storage/`. These files are intentionally excluded from the repository. Only `.gitkeep` placeholders are committed.

## Security

Do not commit real API credentials, databases, sessions, generated user images, or avatars. See `SECURITY.md` for details.
