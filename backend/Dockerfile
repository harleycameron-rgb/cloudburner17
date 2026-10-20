FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && node --input-type=commonjs -e 'const major = Number(process.versions.node.split(".")[0]); if (major < 18) { console.error("Node.js >=18 required; found " + process.versions.node); process.exit(1); }' \
    && rm -rf /var/lib/apt/lists/*

COPY package.json ./
COPY backend/ backend/
COPY src/ src/

RUN pip install -c backend/constraints-ci.txt -r backend/requirements.txt

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--log-level", "critical"]
