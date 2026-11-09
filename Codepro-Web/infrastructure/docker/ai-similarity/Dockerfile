FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir "fastapi>=0.111,<1" "uvicorn>=0.29,<1"
COPY backend/anti_cheat/__init__.py backend/anti_cheat/__init__.py
COPY backend/anti_cheat/services/__init__.py backend/anti_cheat/services/__init__.py
COPY backend/anti_cheat/services/similarity.py backend/anti_cheat/services/similarity.py
COPY apps/ai-similarity/main.py apps/ai-similarity/main.py
USER 65532:65532
ENV PYTHONPATH=/app
WORKDIR /app/apps/ai-similarity
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
