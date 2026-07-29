# Backend — Lexora AI Tone Studio

FastAPI + Gemini engine implementing the Project 2 brief: dynamic prompt
template compilation, temperature/top_p control, async dual-pipeline
(real-time + bulk CSV), retry with backoff, and a standalone CLI.

## 1. Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and paste your Gemini API key (free at
https://aistudio.google.com/apikey) into `GEMINI_API_KEY`.

## 2. Run the API server (for the React frontend)

```bash
uvicorn app.main:app --reload --port 8000
```

API docs will be live at http://localhost:8000/docs

## 3. Or run the CLI directly (no frontend needed)

```bash
python cli.py \
  --product "Aurora Wireless Earbuds" \
  --description "Noise-cancelling earbuds with 30-hour battery life and IPX5 water resistance" \
  --platform linkedin \
  --tone witty \
  --temperature 0.7 \
  --top-p 0.9 \
  +verbose
```

Save straight to a file instead of stdout:

```bash
python cli.py --product "Aurora Earbuds" --description "..." \
  --platform twitter --tone bold -o result.json
```

## 4. Bulk / CSV mode

Start the server, then either:

- Use the "Bulk Mode" panel in the frontend to upload a CSV, or
- Call the endpoint directly:

```bash
curl -X POST http://localhost:8000/api/bulk/generate \
  -F "file=@products.csv"
```

Download a starter template:

```bash
curl http://localhost:8000/api/bulk/template -o bulk_template.csv
```

CSV columns required: `product_name, product_description, platform, tone`
(optional: `temperature, top_p`).
