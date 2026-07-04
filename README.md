# Carnegie Mellon University Course Scheduling Assistant

*95-731 — Group 2*

A Django web app that answers course-scheduling questions with OpenAI's API,
grounded in a reference text file stored in an OpenAI vector store. Ask via
the web form at `/` or via `POST /api/ask/` with `{"question": "..."}`.

See [architecture.md](architecture.md) for the full design and AWS plan.

## Getting started

Prerequisite: [Docker](https://www.docker.com/products/docker-desktop/)
(running). Nothing else needs to be installed or configured.

### Option A — VS Code devcontainer (recommended for development)

1. Open this folder in VS Code and click **"Reopen in Container"** when
   prompted (or run the *Dev Containers: Reopen in Container* command).
2. Wait for the container build + `postCreateCommand` to finish (it installs
   dependencies, creates `.env` from the template if missing, and migrates).
3. In the container terminal:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
4. Open http://localhost:8000

### Option B — plain Docker Compose

```bash
cp .env.example .env   # first time only
docker compose up --build
```

Then open http://localhost:8000

### Enable the AI

The app runs without a key but will return a friendly error until you:

1. Put your OpenAI API key in `.env` (`OPENAI_API_KEY=sk-...`).
2. Put your reference material in `reference/knowledge.txt` and upload it:
   ```bash
   python manage.py upload_reference
   ```
3. Copy the printed `OPENAI_VECTOR_STORE_ID=...` line into `.env` and restart
   the server.

### Try the API

```bash
curl -X POST http://localhost:8000/api/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the reference document say about X?"}'
```

### Run the tests

```bash
python manage.py test
```
