# AI SRE Demo Application Dockerfile
# Multi-stage build for a minimal production image

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY main.py .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PORT=8080
ENV FORCE_HEALTHY=false

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--timeout", "60", "main:app"]
