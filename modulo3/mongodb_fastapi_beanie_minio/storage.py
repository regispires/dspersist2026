import os
import logging

import aioboto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

MINIO_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "avatars")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")

logger = logging.getLogger(__name__)

_session = aioboto3.Session()


def _client():
    return _session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT_URL,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name=MINIO_REGION,
    )


async def ensure_bucket() -> None:
    async with _client() as s3:
        try:
            await s3.head_bucket(Bucket=MINIO_BUCKET)
            logger.info(f"MinIO bucket '{MINIO_BUCKET}' already exists")
        except ClientError:
            await s3.create_bucket(Bucket=MINIO_BUCKET)
            logger.info(f"MinIO bucket '{MINIO_BUCKET}' created")


async def upload_avatar(object_key: str, data: bytes, content_type: str) -> None:
    async with _client() as s3:
        await s3.put_object(
            Bucket=MINIO_BUCKET,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )


async def download_avatar(object_key: str) -> tuple[bytes, str]:
    async with _client() as s3:
        resp = await s3.get_object(Bucket=MINIO_BUCKET, Key=object_key)
        content_type = resp.get("ContentType", "application/octet-stream")
        data = await resp["Body"].read()
        return data, content_type


async def delete_avatar(object_key: str) -> None:
    async with _client() as s3:
        await s3.delete_object(Bucket=MINIO_BUCKET, Key=object_key)
