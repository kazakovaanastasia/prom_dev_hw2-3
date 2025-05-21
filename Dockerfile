FROM python:3.10-alpine3.16

RUN apk update && \
    apk add --no-cache curl tar gcc musl-dev && \
    apk add --no-cache nano && \
    apk del nano

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --progress-bar off

RUN mkdir -p /srv/journals && \
    adduser -D appuser && \
    chown -R appuser:appuser /srv

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]