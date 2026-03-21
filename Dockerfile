# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (e.g., for psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project
COPY backend/ /app/backend/

# Set working directory to where manage.py is
WORKDIR /app/backend

# Optional: Run collectstatic during build (requires dummy env vars if decouple relies on them)
RUN SECRET_KEY='dummy-key-for-build' \
    DATABASE_URL='sqlite:///:memory:' \
    REDIS_URL='redis://localhost:6379/1' \
    DEBUG=False \
    ALLOWED_HOSTS='localhost' \
    FRONTEND_URL='http://localhost:3000' \
    CLIENT_ID='dummy' \
    CLIENT_SECRET='dummy' \
    REDIRECT_URI='dummy' \
    python manage.py collectstatic --noinput

# Expose port 8000 for the app
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
