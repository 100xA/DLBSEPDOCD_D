# --- Build Stage ---
FROM python:3.11-slim as builder

# Install uv, the package manager
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:$PATH"

# Set up the working directory
WORKDIR /app

# Copy dependency files and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

# --- Final Stage ---
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m -d /home/appuser -s /bin/bash appuser
USER appuser
WORKDIR /home/appuser/app

# Copy installed dependencies from the builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code from the builder stage
COPY --from=builder /app .

# Expose the port the app runs on
EXPOSE 8000

# Set the path to include the installed packages
ENV PATH="/root/.local/bin:$PATH"

# Command to run the application (using gunicorn as an example)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "devops_pipeline.wsgi:application"] 