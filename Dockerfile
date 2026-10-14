# Convenience build. The exact runtime is pinned, but this tag is not digest-pinned.
# Resolve and record a verified image digest before freezing a paper release.
FROM python:3.12.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
ENV PYTHONPATH=/app/src
ENTRYPOINT ["python", "-m", "lifecycle_mapper"]
