import os
import psycopg
from loguru import logger
import sys

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def init_db():
    """Initialize the database by executing the create_tables.sql script."""
    conn = None
    try:
        logger.info(f"Attempting to connect to the database at {DB_HOST}:{DB_PORT}...")
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True  # Enable autocommit for DDL statements
        logger.info("Connected to the database!")

        cwd = os.getcwd()
        sql_file_path = os.path.join(cwd, "db", "migrations", "create_tables.sql")

        with open(sql_file_path, "r") as f:
            sql_commands = f.read()

        with conn.cursor() as cursor:
            cursor.execute(sql_commands)
            logger.info("Database initialized successfully!")

    except Exception as e:
        logger.error(f"Error initializing the database: {e}", exc_info=True)
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    init_db()