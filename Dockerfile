FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
COPY pyproject.toml .
RUN pip install -e .

ENV OLLAMA_HOST=http://host.docker.inernal:11434
EXPOSE 8000

CMD ["uvicorn", "luna.main:app", "--host", "0.0.0.", "--port", "8000"]

