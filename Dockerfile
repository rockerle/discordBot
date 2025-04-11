FROM python:3.11-slim

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "-m", "http.server", "8000"]