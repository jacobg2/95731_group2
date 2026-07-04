# CLAUDE.md

"Carnegie Mellon University Course Scheduling Assistant" — Django AI chat
app for CMU 95-731 (Group 2). Answers questions via OpenAI's Responses API
with `file_search` against a vector store holding an uploaded reference
text file. Branding: CMU red `#a6192e` (CSS var `--cmu-red` in the chat
template).

## Commands

All run inside the devcontainer or `docker compose run --rm web <cmd>`:

- `python manage.py runserver 0.0.0.0:8000` — dev server
- `python manage.py test` — test suite (mocks OpenAI; no key needed)
- `python manage.py upload_reference [path]` — upload reference file to the
  OpenAI vector store (default path: `reference/knowledge.txt`); prints the
  store id to put in `.env` as `OPENAI_VECTOR_STORE_ID`
- `ruff check . && ruff format .` — lint/format (config in `pyproject.toml`)

## Layout

- `config/` — Django project (settings read everything from `.env` via
  python-dotenv; see `.env.example` for the full variable list)
- `chat/` — the single app:
  - `views.py` — `index` (form page at `/`) and `api_ask`
    (`POST /api/ask/`, csrf-exempt JSON)
  - `services.py` — **the only module that calls OpenAI**; raises
    `AssistantError` on any failure. Views/tests depend on this boundary —
    keep OpenAI SDK usage out of views.
  - `management/commands/upload_reference.py` — vector store setup
- `Dockerfile` — one image for devcontainer and deployment
  (gunicorn CMD; compose overrides with runserver)
- `.devcontainer/devcontainer.json` — uses docker-compose service `web`,
  installs dev deps + migrates in postCreateCommand

## Conventions

- Secrets/config only via `.env` (gitignored); never hardcode. Add new
  variables to `.env.example` too, with a comment.
- No models/DB usage yet — SQLite exists only for Django's built-in apps.
- Error contract: API returns 400 for bad input, 502 for OpenAI failures,
  always JSON with an `error` key; the form page shows errors inline.
- Update `provenance.md` when adding files (agent vs human authorship log).
- Deployment target is AWS Academy Learner Sandbox (EC2 + Docker); keep
  dependencies minimal and the image close to production (see
  `architecture.md`).
