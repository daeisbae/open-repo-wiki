from tempfile import NamedTemporaryFile
from typing import Optional

import boto3

from db.config.config import DBConfig
import asyncpg
from loguru import logger


async def download_certificate() -> str:
    """
    Asynchronously downloads the certificate from S3 using boto3.
    (boto3 isn't truly async. For real async, consider aioboto3 or a custom approach.)
    """
    s3_client = boto3.client(
        "s3",
        region_name=DBConfig["certificate_region"],
        endpoint_url=DBConfig["certificate_link"],  # If you have a custom endpoint
        aws_access_key_id=DBConfig["certificate_access_key_id"],
        aws_secret_access_key=DBConfig["certificate_secret_access_key"],
    )

    try:
        # This call is blocking in boto3, so if you truly need async S3, see aioboto3
        response = s3_client.get_object(
            Bucket=DBConfig["certificate_bucket"],
            Key=DBConfig["certificate_file"]
        )
        certificate_data = response["Body"].read().decode("utf-8")
        return certificate_data
    except Exception as e:
        logger.critical("Failed to download certificate:", e)
        raise e

class AsyncDBConnector:
    """
    Async database connection handler with a singleton-like pattern.
    Instead of using __init__ for heavy-lifting, we use an async factory method init().

    Usage:
        db = await AsyncDBConnector.init()
        rows = await db.query("SELECT 1")
    """

    _instance: Optional["AsyncDBConnector"] = None

    def __init__(self):
        """Prevent direct instantiation; use init() classmethod."""
        self._pool = None
        self._connected = False
        self._temp_file = None  # For storing the cert if needed.

    @classmethod
    async def init(cls) -> "AsyncDBConnector":
        """
        Asynchronously initializes the connection pool (singleton).
        """
        if cls._instance is not None:
            return cls._instance

        self = cls()
        await self._create_pool()
        cls._instance = self
        return self

    async def _create_pool(self):
        """
        Internal method to create the asyncpg pool. If a certificate is provided, enable SSL.
        """
        host = DBConfig["host"]
        port = DBConfig["port"]
        database = DBConfig["database"]
        user = DBConfig["user"]
        password = DBConfig["password"]
        need_certificate = (
                DBConfig["certificate_link"] and DBConfig["certificate_bucket"]
        )

        ssl_context = None
        if need_certificate:
            try:
                cert_contents = await download_certificate()
                # Save to a temp file
                self._temp_file = NamedTemporaryFile(delete=False)
                self._temp_file.write(cert_contents.encode("utf-8"))
                self._temp_file.flush()

                # asyncpg's SSL usage requires an SSL context from the standard library
                import ssl
                ssl_context = ssl.create_default_context(cafile=self._temp_file.name)
                # If you do not want to validate CA, you could use:
                # ssl_context.check_hostname = False
                # ssl_context.verify_mode = ssl.CERT_NONE

            except Exception as e:
                logger.critical("SSL certificate download or setup failed:", e)
                raise e

        try:
            self._pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                ssl=ssl_context,
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            self._connected = True
            logger.info("AsyncPG pool created successfully.")
        except Exception as e:
            logger.error(f"Error creating asyncpg pool: {e}")
            raise e

    async def query(self, sql: str, params=None):
        """
        Executes an async SQL query with optional parameters.
        Returns a list of record dictionaries.
        """
        if not self._pool or not self._connected:
            raise ConnectionError("No active asyncpg pool connection.")

        if params is None:
            params = []

        async with self._pool.acquire() as conn:
            try:
                # asyncpg returns lists of Record. You can convert each record to dict.
                records = await conn.fetch(sql, *params)
                # Convert each asyncpg.Record to a dict so it’s easier to handle.
                if records is not None and records.__len__() > 0:
                    return [dict(r) for r in records]
                return []
            except Exception as e:
                logger.error(f"Database query failed: {e}")
                raise e