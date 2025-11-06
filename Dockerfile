FROM python:3.12-alpine

ARG FLADO_DATABASE_URI=sqlite:////app/instance/flado.sqlite

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=flado.app:create_app \
    FLADO_DATABASE_URI=${FLADO_DATABASE_URI}

WORKDIR /app

RUN addgroup -S app && adduser -S app -G app

# Install curl for healthcheck
RUN apk add --no-cache curl

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/instance && chown -R app:app /app/instance

VOLUME ["/app/instance"]

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail --silent --show-error http://localhost:5000/health || exit 1

CMD ["sh", "-c", "mkdir -p /app/instance && flask db upgrade && gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 --access-logfile - --error-logfile - wsgi:app"]
