# AI Support Agent

A multi-tenant, B2B customer support platform that answers customers using **only your company's own documents** — via Retrieval-Augmented Generation (RAG), not fine-tuning. Companies upload their docs (PDF, DOCX, CSV, JSON, Markdown, plain text), and the agent answers customer questions over **Website Chat, WhatsApp, and Email** using that knowledge base.

Built with Django + django-ninja, backed by Postgres/pgvector for vector search and Celery/Redis for async processing. Designed to run on free-tier AI services: **Groq** for chat completions and a local **sentence-transformers** model for embeddings (no OpenAI billing required).

## How it works

```
Customer question (Web / WhatsApp / Email)
        │
        ▼
Embed question locally (sentence-transformers, 384-dim)
        │
        ▼
Cosine-similarity search over that company's DocumentChunks
        │
        ▼
Inject top-k matching chunks into a system prompt
        │
        ▼
Groq (Llama 3.1 8B Instant) generates the answer
        │
        ▼
Reply sent back over the originating channel
```

Every document, conversation, and message is scoped to a `Company`, so one deployment can serve many tenants with strict data isolation.

## Features

- **Multi-channel support** — website chat widget, WhatsApp (via Twilio), and inbound/outbound email
- **Document ingestion** — PDF, DOCX, TXT, CSV, JSON, Markdown, and pasted text, chunked and embedded asynchronously via Celery
- **RAG-based answers** — responses are grounded in the company's own knowledge base, with a graceful "I don't know" fallback instead of hallucinating
- **Multi-tenancy** — every company gets an isolated knowledge base, conversation history, and API key
- **Dashboard** — login/signup, document upload, conversation history viewer, and settings, all server-rendered with Django templates
- **REST API** — documented with Swagger UI at `/api/docs`, authenticated via per-company Bearer API keys
- **Health check endpoint** — `/health/` reports database and Redis connectivity for monitoring
- **Free-tier friendly** — Groq for LLM calls and a local embedding model mean you can run this without an OpenAI budget; an OpenAI fallback path exists if you'd rather use it

## Tech stack

| Layer | Technology |
|---|---|
| Framework | Django 5 + django-ninja (REST API + OpenAPI docs) |
| Database | PostgreSQL + pgvector |
| Task queue | Celery + Redis |
| LLM | Groq (`llama-3.1-8b-instant`), OpenAI fallback |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, 384-dim) |
| Messaging | Twilio (WhatsApp) |
| Email | SMTP (Gmail) with Resend as a backup provider |
| Document parsing | pypdf, python-docx |
| Testing | pytest, pytest-django, factory-boy |

## Project layout

```
apps/
├── companies/       # Multi-tenancy, auth, dashboard views
├── knowledge/       # Document upload, chunking, embeddings
├── conversations/   # Chat API, RAG logic (Groq + local embeddings)
└── channels/        # WhatsApp & email webhooks
config/              # Django settings, URLs, Celery config
templates/           # Dashboard, auth, and chat widget templates
tests/               # pytest suite (email flow, Gmail, factories)
```

See [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) for the full architecture write-up, database schema, and day-by-day build log.

## Getting started

### Prerequisites
- Python 3.11+
- Docker Desktop (for PostgreSQL + Redis)
- A [Groq API key](https://console.groq.com) (free tier is enough to run this)

### 1. Clone and install

```bash
git clone https://github.com/Benjaminofili/ai_support_agent
cd ai_support_agent
python -m venv venv
venv\Scripts\activate          # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
```

### 2. Start Postgres + Redis

```bash
docker-compose up -d
```

### 3. Configure environment

```bash
cp .env.example .env
```

At minimum, set `SECRET_KEY` and `GROQ_API_KEY`. WhatsApp (Twilio) and email (SMTP/Resend) settings are optional — the app works with website chat alone if they're left blank.

### 4. Run migrations and start the server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 5. Start the Celery worker (separate terminal)

Document processing and message handling run asynchronously, so Celery must be running for uploads and chat replies to complete:

```bash
venv\Scripts\activate
celery -A config worker --loglevel=info --pool=solo
```

Visit `http://localhost:8000` to sign up, create a company, upload a document, and start chatting. API docs are at `http://localhost:8000/api/docs`.

## Environment variables

| Variable | Purpose | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Enables debug mode | Dev only |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | Yes (prod) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis/Celery broker URL | Yes |
| `GROQ_API_KEY` | Groq API key for chat responses | Yes (or OpenAI) |
| `OPENAI_API_KEY` | Optional fallback LLM/embeddings provider | No |
| `EMBEDDING_MODEL` | HuggingFace model for local embeddings | No (defaults to MiniLM-L6-v2) |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` | WhatsApp integration | Only if using WhatsApp |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Backup email provider | No |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_HOST`, `EMAIL_PORT` | SMTP email sending | Only if using email |
| `CHUNK_SIZE`, `CHUNK_OVERLAP`, `MAX_TOKENS`, `MAX_CONTEXT_CHUNKS` | RAG tuning knobs | No |

Full list with defaults: [.env.example](.env.example).

## API overview

All API endpoints live under `/api/` and require a per-company Bearer token (`Authorization: Bearer <api_key>`, found on the company record). Interactive docs: `/api/docs`.

```
/api/knowledge/
  POST   /documents/upload/          Upload a document (file or pasted text)
  GET    /documents/                 List documents for the authenticated company
  GET    /documents/{id}/            Get a document's processing status
  DELETE /documents/{id}/            Delete a document and its chunks

/api/chat/
  POST   /message/                   Send a message, get an AI-generated reply
  GET    /conversations/             List conversations
  GET    /conversations/{id}/messages/   Get a conversation's message history

/api/webhooks/
  POST   /whatsapp/                  Twilio inbound WhatsApp webhook
  POST   /email/                     Inbound email webhook

/health/                             Database + Redis health check
```

## WhatsApp & email setup

- **WhatsApp**: create a Twilio account, enable the WhatsApp Sandbox, and point its webhook at `https://<your-domain>/api/webhooks/whatsapp/`. For local development, expose your server with `ngrok http 8000` and use the generated HTTPS URL.
- **Email**: configure `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` for outbound SMTP, and point your inbound email provider's webhook at `/api/webhooks/email/`.

## Docker

```bash
docker-compose up -d          # Postgres (pgvector) + Redis
docker build -t ai_support_agent .
docker run -p 8000:8000 ai_support_agent
```

`docker-compose.yml` runs the data layer only (Postgres + Redis); the Dockerfile builds the Django app image separately. See [docker_commands.txt](docker_commands.txt) for common day-to-day commands.

## Testing

```bash
python manage.py test
# or
pytest
```

The `tests/` directory covers the email flow (Gmail SMTP, inbound processing) and includes `factory-boy` factories for generating test companies, documents, and conversations.

## Status

This started as a solo, time-boxed academic project (see the day-by-day log in [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)) and is under active iteration — expect some rough edges around production hardening (rate limiting, request validation, and multi-worker embedding model loading are good next steps for anyone extending it).
