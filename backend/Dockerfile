FROM python:3.11-slim

WORKDIR /app

COPY backend/ backend/
COPY src/ src/

RUN pip install -r backend/requirements.txt

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
