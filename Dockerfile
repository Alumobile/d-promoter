FROM cgr.dev/chainguard/python:latest-dev as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY --from=builder /home/nonroot/.local/lib/python3.12/site-packages /home/nonroot/.local/lib/python3.12/site-packages

# Copia os certificados SSL para o container
COPY certs/server.crt /app/certs/server.crt
COPY certs/server.key /app/certs/server.key
COPY d-promoter.py /app/d-promoter.py

EXPOSE 5000

ENTRYPOINT [ "python", "/app/d-promoter.py" ]
