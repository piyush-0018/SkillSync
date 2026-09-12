# Deployment and operations

## Selected zero-cost demo topology

SkillSync uses one Render Free web service for the compiled React frontend and FastAPI API, Neon Free for PostgreSQL plus pgvector, and the Gemini API free tier for structured generation and embeddings. Serving the SPA and API from one origin preserves the existing secure-cookie design and avoids a separate frontend proxy.

This is appropriate for a portfolio demonstration, not a production SLA. Render can sleep after inactivity and its filesystem is ephemeral. Neon and Gemini enforce free quotas. Provider pricing and limits can change, so verify them before deployment.

## Local setup without Docker

Create a PostgreSQL database and a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey). Then copy `backend/.env.example` to `backend/.env` and configure `DATABASE_URL`, a generated `JWT_SECRET`, and `GEMINI_API_KEY`.

```powershell
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Start the Vite frontend separately using the instructions in the root README.

## Local Docker Compose

Compose runs PostgreSQL with pgvector, migrations, and the combined application image. Gemini remains an external API.

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32)); print(secrets.token_hex(32))"
docker compose config --quiet
docker compose up --build -d
docker compose logs --tail 50 app migrate
```

Put the generated database password and JWT secret in root `.env`, along with `GEMINI_API_KEY`. Open `http://localhost:8000`. `docker compose down` retains the database and stored PDFs. Do not use `down -v` unless permanent deletion of local data is intended.

## Neon database

1. Create a free Neon project and copy its pooled PostgreSQL connection string.
2. Connect using the Neon SQL editor and run `CREATE EXTENSION IF NOT EXISTS vector;`.
3. Store the connection string as Render's `DATABASE_URL`. Do not commit it.
4. Keep the database in the same broad region as the Render service where possible.

The application normalizes ordinary `postgres://` and `postgresql://` URLs for psycopg. The current vector implementation stores vectors as JSON and uses pgvector expressions for exact ranking; it does not use an approximate vector index.

## Render deployment

1. Fork or connect the public SkillSync GitHub repository to Render.
2. Create a Blueprint from `render.yaml` and confirm that the service plan is **Free**.
3. Set `DATABASE_URL` to the Neon URL and `GEMINI_API_KEY` to the Google AI Studio key.
4. Set `FRONTEND_ORIGIN` to the exact assigned Render HTTPS URL, without a path or trailing slash.
5. Deploy from the repository root. The Docker build needs both `frontend` and `backend`.
6. Confirm the migration step, `/api/health`, `/api/ready`, registration, login, PDF upload and each AI workflow.

The Blueprint stores uploads in `/tmp/skillsync-resumes`. Raw PDFs disappear when the free instance restarts, while extracted resume text and analysis records remain in Neon. Resume replacement and deletion tolerate an already-missing file. Use private object storage before accepting real user documents.

Render's first request after idle sleep may be slow. Do not add a paid plan, persistent disk, database, or billing method merely to avoid that limitation unless the owner explicitly approves it.

## Gemini configuration and privacy

The API key is used only by FastAPI and must never be placed in `VITE_*`, frontend code, screenshots, logs, Docker build arguments, or Git. The configured models are:

- `gemini-3.1-flash-lite` for structured generation.
- `gemini-embedding-001` with 768 output dimensions for RAG and job similarity.

Changing the embedding model or dimensions causes stored career documents to be re-indexed. Existing persisted model results remain in history and are labeled with their provider/model metadata.

Gemini free-tier request content may be used by Google to improve its products. The public portfolio deployment must therefore use fictional or synthetic resumes and job descriptions unless a separate consent and data-handling policy is introduced.

## Operations and rollback

- Run `python -m alembic upgrade head` before starting a release that requires a schema change.
- Keep database credentials, JWT secrets, and the Gemini key only in host secret settings.
- Rotate a key immediately if it appears in source, logs, screenshots, or browser-delivered assets.
- Check Render logs using request IDs; logs intentionally omit request bodies and cookies.
- Roll back application code to a tested commit. Database downgrades require reviewing the relevant Alembic migration and backing up data first.
- Export Neon data before material schema changes. The free plan is not a substitute for a tested backup policy.

## Verification

```powershell
cd backend
.venv/Scripts/python.exe -m pytest tests -q
cd ../frontend
npm run lint
npm run build
```

For the optional real PostgreSQL vector test, set `TEST_POSTGRES_URL` to a disposable pgvector-enabled database and run `tests/test_pgvector_integration.py`. Never point destructive or test tooling at production.
