FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1

COPY backend/ backend/
COPY src/ src/

RUN pip install -r backend/requirements.txt

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--log-level", "critical"]
