# CodeFix AI Premium Studio — Implementation Notes

## Frontend

- Full-height chatbot workspace with responsive navigation.
- New Review action, searchable review history, saved review sessions, and active-session restoration.
- Profile footer with settings access.
- File attachment and code-paste workflows.
- Structured assistant response with Overview, Findings, Corrected Code, and Line-by-Line tabs.
- Syntax highlighting, line numbers, copy, and corrected-file download.
- Professional loading, success, clean-code, and failure states.
- Workspace preferences for review focus, analysis depth, automatic explanation, profile identity, and history management.
- Supplied CodeFix logo integrated into the sidebar, assistant avatar, welcome state, browser icon, and brand system.

## Backend

- Existing deterministic `BUG_REPORT` and `REFACTORED_CODE` validation preserved and strengthened.
- Review focus and analysis-depth controls added.
- New `/api/explain` endpoint with validated summary, execution flow, line-by-line, and key-concept sections.
- File ingestion handling improved for UTF-8 source files, safe filenames, size limits, and professional API errors.

## Run

1. Configure `backend/.env` from `backend/.env.example`.
2. Install backend requirements and run `uvicorn main:app --reload --port 8000`.
3. Install frontend packages and run `npm run dev`.
