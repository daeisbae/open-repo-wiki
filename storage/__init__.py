"""Shared storage clients for AWS services."""

from shared.storage.dynamodb import DynamoDBClient
from shared.storage.s3 import S3Client

__all__ = [
    "DynamoDBClient",
    "S3Client",
]
