# Oryn — Prism AI Assistant

Oryn is a clean, modern AI chatbot workspace inspired by the best parts of ChatGPT, Claude, and Gemini. It includes a real FastAPI backend, saved chat history, a professional responsive frontend, dark/light mode, export, rename, clear chat, and reliable error handling.

## Features

- Professional sidebar with recent chats
- New chat, rename chat, clear chat, export chat
- Persistent local chat storage in `backend/data/chats.json`
- FastAPI backend with Gemini model support
- Friendly demo mode if the API key is not configured
- Responsive mobile layout
- Clean message rendering with code blocks and copy buttons
- Dark/light mode
- Health/status indicators

## Run locally

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
# edit .env and add GEMINI_API_KEY
uvicorn app:app --reload --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

## Important

Do not upload or share your real `.env` file. This ZIP includes only `.env.example`, not a real API key.


## Correct backend run command
Open PowerShell inside `backend` and run:

```powershell
python -m uvicorn main:app --reload
```

`main.py` is the primary ASGI entry file. `app.py` is also included for compatibility, but `main:app` is the safest command.

Then open:

```text
http://127.0.0.1:8000
```

## If you see Request failed (405) or Backend unavailable

This means the frontend was opened from a static preview server or old folder, so API requests did not reach FastAPI.

Use one of these safe options:

1. Run `start_windows.bat` from the project root and open `http://127.0.0.1:8000`.
2. Or run:
   ```powershell
   cd backend
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
   Then open `http://127.0.0.1:8000`.

The frontend now automatically falls back to `http://127.0.0.1:8000` when opened from Live Server, file preview, or another local port.


## Project Identity
- Company: Prism
- Assistant: Oryn
- Built by: Muhammad Saad Jadoon — AI Engineer, Artificial Intelligence Developer, Machine Learning Enthusiast, Full Stack Web Developer, Technical SEO Strategist, and Social Media Marketing Specialist. He studies at the University of Haripur and received a laptop from Prime Minister Shehbaz Sharif on Dec 17, 2025 based on his high academic record.
