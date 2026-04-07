FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all project files (needed for openenv validate to work inside)
COPY . .

# Environment defaults (Hugging Face Spaces use 7860)
ENV PORT=7860
ENV PYTHONPATH=/app
ENV ENABLE_WEB_INTERFACE=false

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
