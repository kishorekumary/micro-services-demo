FROM python:3.11
WORKDIR /app

RUN pip install fastapi uvicorn pika psycopg2-binary redis python-multipart dotenv minio pydantic elasticsearch==8.15.0
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]