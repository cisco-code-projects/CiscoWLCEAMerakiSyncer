FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required (e.g. for cryptography)
# build-essential can be removed if not needed for specific wheels, but good for safety.
# RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables should be passed at runtime, but we can set defaults
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "main.py"]
