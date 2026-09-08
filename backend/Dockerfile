FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

# The frontend prototype is the visual contract served by the API at /
# and /static/*. It sits next to the backend at /app/frontend.
COPY frontend /app/frontend

EXPOSE 8000

# Migration bootstrap entrypoint: waits for PostgreSQL readiness, then applies
# `alembic upgrade head` before handing off to the API command.
ENTRYPOINT ["python", "/app/docker-entrypoint.py"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
