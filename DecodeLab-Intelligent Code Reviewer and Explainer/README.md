# CodeFix AI — Code Intelligence Studio

A professional AI-powered code reviewer and explainer built for DecodeLabs Generative AI Project 4.

## Capabilities

- Upload source files or paste code directly.
- Review Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, Ruby, PHP, SQL, HTML, CSS and more.
- Return a strictly validated `BUG_REPORT` and complete `REFACTORED_CODE` block.
- Preserve correct code unchanged when no defects are found.
- Render corrected output with syntax highlighting, copy, and download actions.
- Generate an optional line-by-line explanation with execution flow and key concepts.
- Chat-style review workspace with searchable server-backed history, new-review sessions, profile, and preferences.

## Run the backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Add GEMINI_API_KEY to backend/.env
uvicorn main:app --reload --port 8000
```

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Workspace persistence

Review history, appearance, review preferences, profile details, and profile images are stored by the FastAPI backend in SQLite. Each browser/device receives an anonymous secure workspace identifier so its data remains separate without storing review content in browser storage.

The header appearance control switches between complete dark and light themes and saves the selection to the backend.

## Validation architecture

The review model is constrained to return exactly:

```text
## BUG_REPORT
## REFACTORED_CODE
```

The backend validates both sections before returning the result. A malformed response is retried once with stricter instructions and is rejected if it remains invalid. The explanation workflow similarly validates its required summary, execution-flow, line-by-line, and key-concept sections.
