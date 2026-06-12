# ==============================================================================
# STAGE 1: Builder (Compile dependencies)
# ==============================================================================
FROM python:3.11-slim as builder

# Prevent python from writing bytecode (.pyc) and keep stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install system compilation packages (needed for compiling packages like bcrypt/cryptography if wheels aren't used)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ==============================================================================
# STAGE 2: Final minimal production image
# ==============================================================================
FROM python:3.11-slim as final

# Prevent python from writing bytecode, keep output unbuffered, and configure paths
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Create a dedicated non-root group and user for container runtime security (Least Privilege Principle)
# Using a system user without a home directory and no shell access (/usr/sbin/nologin)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup --system --no-create-home -s /usr/sbin/nologin appuser

WORKDIR /app

# Copy the virtual environment from builder stage with correct ownership
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy application source code with correct ownership
COPY --chown=appuser:appgroup ./app /app/app
COPY --chown=appuser:appgroup ./alembic /app/alembic
COPY --chown=appuser:appgroup ./alembic.ini /app/alembic.ini
COPY --chown=appuser:appgroup ./run.py /app/run.py

# Switch runtime to the non-root user
USER appuser

# Document ports intended to be mapped
EXPOSE 8000

# Docker Healthcheck targeting FastAPI's health check route
# Using python's urllib avoids adding curl/wget, keeping the image minimal and secure
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()"

# Start the application using uvicorn under the virtual environment's path
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
