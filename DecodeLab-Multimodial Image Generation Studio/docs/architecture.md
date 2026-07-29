# Prismora Architecture

Prismora is delivered as a single FastAPI application. FastAPI serves both the API and the static frontend, which avoids a separate frontend server and CORS configuration during local development.

## Runtime flow

1. The browser loads the UI from `backend/static/`.
2. Authentication, settings, threads, generations, favorites, and profile data are handled by routes in `backend/main.py`.
3. Gemini is used for prompt enhancement and visual quality review when configured.
4. Cloudflare Workers AI FLUX.1 Schnell generates the requested image.
5. `backend/quality_pipeline.py` handles input moderation, binary streaming, image decoding, dimension normalization, output safety, and quality evaluation.
6. SQLite stores application records locally. Generated images and avatars are written under `backend/storage/` at runtime.

## Important directories

- `backend/static/`: browser interface and brand assets.
- `backend/storage/`: runtime-only database, generated images, avatars, logs, and temporary files.
- `backend/tests/`: active-backend automated tests.
- `scripts/`: setup and launch helpers.

Runtime data is intentionally excluded from Git by `.gitignore`.
