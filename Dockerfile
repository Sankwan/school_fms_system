# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE config.settings.production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    default-mysql-client \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create logs and media directories (if they don't exist)
RUN mkdir -p /app/logs /app/media /app/staticfiles

# Create non-root user for security
RUN addgroup --system appuser && adduser --system --group appuser
RUN chown -R appuser:appuser /app

# Ensure entrypoint is executable
RUN chmod +x /app/docker/entrypoint.sh

# Change to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run entrypoint
ENTRYPOINT ["/app/docker/entrypoint.sh"]
