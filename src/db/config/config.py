import os
from dotenv import load_dotenv

load_dotenv()

DBConfig = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "certificate_link": os.getenv("DB_CERTIFICATE_LINK"),
    "certificate_region": os.getenv("DB_CERTIFICATE_REGION"),
    "certificate_bucket": os.getenv("DB_CERTIFICATE_BUCKET_NAME"),
    "certificate_file": os.getenv("DB_CERTIFICATE_FILE"),
    "certificate_access_key_id": os.getenv("DB_CERTIFICATE_ACCESS_KEY_ID"),
    "certificate_secret_access_key": os.getenv("DB_CERTIFICATE_SECRET_ACCESS_KEY"),
}
