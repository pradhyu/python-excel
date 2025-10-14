# Excel DataFrame Processor - Docker Image
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Excel DataFrame Processor Team"
LABEL description="Excel DataFrame Processor CLI with SQL capabilities"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TERM=xterm-256color

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and user
RUN groupadd -r exceluser && useradd -r -g exceluser exceluser
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache-dir -e .

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p /data /app/logs && \
    chown -R exceluser:exceluser /app /data

# Install the package
RUN uv pip install --system --no-cache-dir -e .

# Switch to non-root user
USER exceluser

# Set default database directory
ENV EXCEL_DB_DIR=/data

# Expose port for potential web interface (future use)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import excel_processor; print('OK')" || exit 1

# Default command - start REPL with mounted data directory
CMD ["python", "-m", "excel_processor", "--db", "/data"]