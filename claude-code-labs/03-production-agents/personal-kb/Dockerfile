FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./

# Create data directory
RUN mkdir -p /app/kb_data

# Expose port
EXPOSE 8501

# Environment
ENV KB_PATH=/app/kb_data

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run
CMD ["streamlit", "run", "kb_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
