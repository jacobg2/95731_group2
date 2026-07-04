# Architecture — CMU Course Scheduling Assistant (95-731 Group 2)

## What was built

A Django web application that answers user questions with OpenAI's API,
grounded in a reference text file. Users interact two ways:

1. **Web form** at `/` — type a question, get the answer rendered on the page.
2. **JSON API** at `POST /api/ask/` — send `{"question": "..."}`, receive
   `{"question": "...", "answer": "..."}`. Errors return `400` (bad input) or
   `502` (upstream OpenAI failure) with an `error` field.

Retrieval works through an **OpenAI vector store**: a maintainer runs
`python manage.py upload_reference`, which uploads `reference/knowledge.txt`
to a vector store and prints the store id for `.env`. At question time the
app calls the OpenAI **Responses API** with the `file_search` tool pointed at
that store, so answers are grounded in the uploaded document. All OpenAI
access is isolated in `chat/services.py`; views never touch the OpenAI SDK
directly, which keeps the integration testable (the test suite mocks it) and
swappable.

Configuration (secret key, debug flag, allowed hosts, OpenAI key/model/store
id) is read from a gitignored `.env` file, so the same code runs unchanged on
a laptop, in the devcontainer, or on an AWS instance.

## Component diagram

```
                        ┌──────────────────────────────────────────────┐
                        │        AWS Academy Learner Sandbox           │
                        │  ┌─────────────────────────────────────────┐ │
 ┌──────────┐  HTTP     │  │            EC2 instance                 │ │
 │ Browser  │──────────►│  │  ┌───────────────────────────────────┐  │ │
 │ (form UI)│  :8000    │  │  │        Docker container           │  │ │
 └──────────┘           │  │  │  ┌──────────┐    ┌─────────────┐  │  │ │
                        │  │  │  │ gunicorn │───►│   Django    │  │  │ │
 ┌──────────┐  HTTP     │  │  │  └──────────┘    │ ┌─────────┐ │  │  │ │
 │ API      │──────────►│  │  │        ▲         │ │  chat   │ │  │  │ │
 │ client   │POST       │  │  │        │         │ │  views  │ │  │  │ │
 │ (curl,..)│/api/ask/  │  │  │   .env file      │ └────┬────┘ │  │  │ │
 └──────────┘           │  │  │  (secrets/config)│      ▼      │  │  │ │
                        │  │  │                  │ ┌─────────┐ │  │  │ │
                        │  │  │                  │ │services │ │  │  │ │
                        │  │  │                  │ │  .py    │ │  │  │ │
                        │  │  │                  │ └────┬────┘ │  │  │ │
                        │  │  │                  └──────┼──────┘  │  │ │
                        │  │  └─────────────────────────┼─────────┘  │ │
                        │  └────────────────────────────┼────────────┘ │
                        │     Security group (80/8000)  │              │
                        └───────────────────────────────┼──────────────┘
                                                        │ HTTPS
                                                        ▼
                                        ┌───────────────────────────┐
                                        │        OpenAI API         │
                                        │  ┌─────────────────────┐  │
                                        │  │ Responses API       │  │
                                        │  │  (chat model)       │  │
                                        │  └──────────┬──────────┘  │
                                        │             │ file_search │
                                        │  ┌──────────▼──────────┐  │
                                        │  │ Vector store        │  │
                                        │  │ (knowledge.txt)     │  │
                                        │  └─────────────────────┘  │
                                        └───────────────────────────┘
```

### Components, one sentence each

| Component | Purpose |
|---|---|
| **Browser / form UI** | Lets a human type a question and read the answer (input: text; output: rendered HTML). |
| **API client** | Any program (curl, grader script, another service) that POSTs JSON questions and consumes JSON answers. |
| **gunicorn** | Production WSGI server that receives HTTP requests and hands them to Django (dev mode uses `runserver` instead). |
| **Django `chat` views** | Validate input from the form or JSON body and render/serialize the response. |
| **`chat/services.py`** | The only module that talks to OpenAI — builds the Responses API call with the `file_search` tool and returns answer text or a typed error. |
| **`.env` file** | Supplies secrets and per-environment config (API key, allowed hosts, vector store id) without code changes. |
| **OpenAI Responses API** | Generates the answer using the configured model, consulting the vector store when configured. |
| **OpenAI vector store** | Holds the embedded reference document (`knowledge.txt`) that grounds answers, populated by the `upload_reference` management command. |
| **Docker container** | Packages Python 3.12, dependencies, and the app identically for the devcontainer and for deployment. |
| **EC2 instance + security group** | Planned AWS host that runs the container and admits inbound HTTP on the app port. |

## AWS services used or planned, and why

The app is not yet deployed; the target is the **AWS Academy Learner
Sandbox**, which restricts IAM and some managed services, so the plan favors
simple primitives available there:

- **EC2 (planned, primary)** — a single small instance (e.g. `t3.small`)
  running Docker. The same image built by our Dockerfile runs here with
  `docker compose up`, so deployment is copy-repo → create `.env` → compose
  up. Chosen because it is the most reliable service in the Learner Sandbox
  and matches our container-first local setup.
- **Security group (planned)** — inbound rules for SSH (22) and the app port
  (80/8000); this is the sandbox's front door instead of a load balancer,
  which a single-instance class project doesn't need.
- **Elastic IP (planned, optional)** — a stable address so `ALLOWED_HOSTS`
  doesn't change every time the sandbox lab restarts.
- **S3 (considered, not needed yet)** — would hold static assets or larger
  reference corpora; today whitenoise serves static files from the container
  and the reference file lives in the OpenAI vector store, so S3 adds no
  value at this scale.
- **RDS (considered, rejected for now)** — the app keeps no chat history, so
  SQLite inside the instance covers Django's minimal needs; RDS becomes
  worthwhile only if we add persistent conversations or multiple instances.
- **Secrets Manager (considered)** — Learner Sandbox IAM limits make it
  awkward; the `.env` file on the instance (never in git) is the pragmatic
  substitute at this scale.

Heavy lifting for retrieval (embedding, chunking, similarity search) is
deliberately outsourced to OpenAI's hosted vector store rather than running
our own vector database — one less service to operate inside a constrained
sandbox.

## Request flow

1. A question arrives via the form (`POST /`) or the API (`POST /api/ask/`).
2. The view validates it (Django form or JSON schema check).
3. `services.ask_question()` calls the OpenAI Responses API with the
   `file_search` tool bound to our vector store.
4. OpenAI retrieves relevant chunks of `knowledge.txt`, generates an answer,
   and the service returns `response.output_text`.
5. The view renders the answer in HTML or wraps it in JSON; upstream
   failures surface as a friendly error message (form) or a `502` (API).
