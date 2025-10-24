FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# default envs; override in Unraid UI
ENV OLLAMA_HOST=http://192.168.0.27:11434 \
    DEFAULT_MD_MODEL=gemma3:12b-it-q8_0 \
    API_PORT=5000

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 tesseract-ocr curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/app.py
EXPOSE 5000
CMD ["sh","-lc","uvicorn app:app --host 0.0.0.0 --port ${API_PORT:-5000}"]

