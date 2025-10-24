import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "orders-bucket")

# Strip scheme for SDK compatibility
endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")

client = Minio(
    endpoint=endpoint,
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
    secure=MINIO_ENDPOINT.startswith("https")
)

def upload_file(file_path: str, object_name: str):
    """Upload a local file to MinIO bucket."""
    found = client.bucket_exists(MINIO_BUCKET)
    if not found:
        client.make_bucket(MINIO_BUCKET)
    client.fput_object(MINIO_BUCKET, object_name, file_path)
    print(f"✅ Uploaded {object_name} to {MINIO_BUCKET}")

def download_file(object_name: str, dest_path: str):
    """Download an object to local path."""
    client.fget_object(MINIO_BUCKET, object_name, dest_path)
    print(f"✅ Downloaded {object_name} to {dest_path}")