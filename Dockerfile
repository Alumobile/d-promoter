FROM cgr.dev/chainguard/python:latest-dev as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --target=/app/site-packages -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY --from=builder /app/site-packages /app/site-packages

COPY certs/server.crt /app/certs/server.crt
COPY certs/server.key /app/certs/server.key
COPY d-promoter.py /app/d-promoter.py

EXPOSE 5000

ENV PYTHONPATH=/app/site-packages

ENTRYPOINT [ "python", "/app/d-promoter.py" ]
