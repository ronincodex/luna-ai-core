FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
COPY pyproject.toml .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /app/src/
RUN pip install -e .
EXPOSE 8000
ENV OLLAMA_HOST=http://host.docker.internal:11434
CMD ["uvicorn", "luna.main:app", "--host", "0.0.0.0", "--port", "8000"]

# FROM python:3.12-slim

# Set the working directory inside the container
# WORKDIR /app

# Install system dependencies (required for some Python packages)
# RUN apt-get update && apt-get install -y --no-install-recommends \
# gcc \
# && rm -rm /var/lib/apt/lists/*

# Copy only requirements first (leverages Docker caching)
# COPY requirements.txt .
# COPY pyproject.toml .

#Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire source code
# COPY src/ /app/src/
# COPY pyproject.toml .

# Install the package in editable mode (so imports like 'luna.main' work)
# RUN pip install -e .

# Set the Ollama host( tells luna to talk to the host machine's Ollama)
# ENV OLLAMA_HOST=http://host.docker.inernal:11434

# Expose the port FastAPI runs on
# EXPOSE 8000

# Run the fastAPI server
# CMD ["uvicorn", "luna.main:app", "--host", "0.0.0.", "--port", "8000"]

