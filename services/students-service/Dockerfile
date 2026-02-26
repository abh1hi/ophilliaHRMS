FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 8003
ENTRYPOINT ["./entrypoint.sh"]
