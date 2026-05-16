FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Copy app code
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY content/ ./content/
COPY contracts/ ./contracts/
COPY docs/hackathon-0g/mainnet-proof.json ./docs/hackathon-0g/mainnet-proof.json

# Expose Flask port
EXPOSE 8109

ENV HOST=0.0.0.0
ENV PORT=8109

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8109/api/healthz || exit 1

# Default: run the production WSGI server
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8109} guard0.app:app"]
