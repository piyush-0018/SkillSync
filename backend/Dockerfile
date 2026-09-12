# Build from the repository root: docker build -f backend/Dockerfile .
FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_URL=/api
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 skillsync
COPY --chown=skillsync:skillsync backend/app ./app
COPY --chown=skillsync:skillsync backend/alembic ./alembic
COPY --chown=skillsync:skillsync backend/alembic.ini backend/serve.py ./
COPY --from=frontend --chown=skillsync:skillsync /build/dist /app/frontend-dist
RUN mkdir -p /app/storage/resumes && chown -R skillsync:skillsync /app/storage
ENV FRONTEND_DIST_DIR=/app/frontend-dist RESUME_STORAGE_DIR=/app/storage/resumes PORT=8000
USER skillsync
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && exec python serve.py"]
