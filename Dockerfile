FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (optional, but good for some packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (leverages Docker caching)
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY src/ /app/src/
COPY static/ /app/static/

# Install the package in editable mode
RUN pip install -e .

# Expose the port FastAPI runs on
EXPOSE 8000

# Set the Ollama host (tells Luna to talk to the host machine's Ollama)
ENV OLLAMA_HOST=http://host.docker.internal:11434

# Run the FastAPI server
CMD ["uvicorn", "luna.main:app", "--host", "0.0.0.0", "--port", "8000"]
