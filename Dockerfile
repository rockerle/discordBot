FROM python:3.11

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "-m", "http.server", "8000"]