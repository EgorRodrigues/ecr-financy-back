# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy files needed for dependency installation
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
