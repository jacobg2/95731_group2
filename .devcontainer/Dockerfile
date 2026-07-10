# Single image used for both the VS Code devcontainer (via docker-compose)
# and a simple production-style deployment (e.g. an EC2 instance in the
# AWS Academy Learner Sandbox).
# Build with the repo root as context: docker build -f .devcontainer/Dockerfile .
# (ignore rules live in Dockerfile.dockerignore next to this file).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# git is needed by the devcontainer for source control inside the container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Production entrypoint; docker-compose overrides this with runserver for
# local development.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
