# Lexora AI Tone Studio

Lexora is a premium AI copywriting and tone transformation workspace powered by FastAPI, React, and Gemini.

## Highlights

- Advanced generation controls: target audience, objective, language, length, keywords, brand voice, emoji level, variations, formality, CTA type.
- Three controlled output versions: Safe, Creative, and Bold.
- Output editor with character/word counts, copy, regenerate, favourite, and download actions.
- Local workspace: recent generations, favourites, saved templates, duplicate generation, filters, and demo profile login.
- Transformation modes: rewrite, shorten, expand, improve, simplify, humanize, grammar fix, professionalize, change tone, headlines, hashtags, and translate.
- Improved platform presets for LinkedIn, Instagram, Facebook, Email, X, Google Ads, YouTube, and TikTok.
- Bulk CSV: drag-and-drop, preview, invalid row highlighting, progress, retry, success/error counts, and CSV export.
- Backend improvements: friendly CSV validation, Gemini permanent/transient error classification, request size guard, simple rate limiting, safer CORS defaults.
- Deployment files: Dockerfile, docker-compose.yml, .dockerignore, GitHub Actions CI, pytest examples.

## Run Backend

```bash
cd backend
cp .env.example .env
# add GEMINI_API_KEY to .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## Production Notes

Do not commit `.env`, `venv`, `node_modules`, `dist`, or cache folders. Configure `FRONTEND_ORIGIN` to your production frontend domain.

## Repository Structure

```text
lexora-ai/
├── .github/workflows/ci.yml   # Backend tests and frontend build
├── backend/
│   ├── app/                   # FastAPI application and Gemini pipeline
│   ├── data/                  # Runtime DB/uploads (ignored by Git)
│   ├── tests/                 # Backend tests
│   ├── cli.py                 # Standalone command-line interface
│   ├── .env.example           # Backend environment template
│   └── requirements.txt
├── frontend/
│   ├── src/                   # React application
│   ├── .env.example           # Frontend environment template
│   ├── package.json
│   └── package-lock.json
├── data/                      # Docker runtime data (ignored by Git)
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── README.md
```

## First-Time Setup

Create local environment files from the committed examples. Never commit the real files.

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend (optional; defaults already target localhost:8000)
cp frontend/.env.example frontend/.env
```

Then place your Gemini key in `backend/.env` and use the backend/frontend commands above.

## Tests

```bash
pip install -r backend/requirements.txt
pytest backend/tests

cd frontend
npm ci
npm run build
```

## Repository Safety

The repository intentionally excludes API keys, virtual environments, `node_modules`, SQLite databases, sessions, profile uploads, caches, and generated build files. The application recreates its runtime data folders and database automatically.

