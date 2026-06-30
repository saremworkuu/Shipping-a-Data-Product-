"""
Load Raw Telegram Data to PostgreSQL

This script reads JSON files from the data lake and loads them into
the raw schema in PostgreSQL.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "medical_warehouse")
DB_PORT = os.getenv("DB_PORT", "5432")

# Data lake path
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
LOGS_DIR = BASE_DIR / "logs"

# Setup logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"load_to_postgres_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create a database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            port=DB_PORT
        )
        logger.info("Successfully connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise


def create_raw_schema(conn):
    """Create the raw schema and telegram_messages table."""
    try:
        cur = conn.cursor()
        
        # Create raw schema
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        
        # Create telegram_messages table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            message_id BIGINT,
            channel_name VARCHAR(255),
            message_date TIMESTAMP,
            message_text TEXT,
            has_media BOOLEAN,
            image_path VARCHAR(500),
            views INTEGER,
            forwards INTEGER,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cur.execute(create_table_sql)
        
        conn.commit()
        logger.info("Created raw schema and telegram_messages table")
        cur.close()
        
    except Exception as e:
        logger.error(f"Error creating schema/table: {e}")
        conn.rollback()
        raise


def read_json_files() -> List[Dict[str, Any]]:
    """
    Read all JSON files from the data lake.
    
    Returns:
        List of all message dictionaries
    """
    all_messages = []
    messages_dir = RAW_DATA_DIR / "telegram_messages"
    
    if not messages_dir.exists():
        logger.warning(f"Data lake directory not found: {messages_dir}")
        return all_messages
    
    # Walk through all date directories
    for date_dir in messages_dir.iterdir():
        if not date_dir.is_dir():
            continue
        
        logger.info(f"Processing date directory: {date_dir.name}")
        
        # Read all JSON files in the date directory
        for json_file in date_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                    all_messages.extend(messages)
                logger.info(f"Loaded {len(messages)} messages from {json_file.name}")
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")
    
    logger.info(f"Total messages loaded: {len(all_messages)}")
    return all_messages


def load_messages_to_db(conn, messages: List[Dict[str, Any]]):
    """
    Load messages into PostgreSQL.
    
    Args:
        conn: Database connection
        messages: List of message dictionaries
    """
    if not messages:
        logger.warning("No messages to load")
        return
    
    try:
        cur = conn.cursor()
        
        # Prepare insert query
        insert_query = """
        INSERT INTO raw.telegram_messages 
        (message_id, channel_name, message_date, message_text, has_media, image_path, views, forwards)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
        """
        
        # Prepare data for batch insert
        data_to_insert = []
        for msg in messages:
            data_to_insert.append((
                msg.get('message_id'),
                msg.get('channel_name'),
                msg.get('message_date'),
                msg.get('message_text'),
                msg.get('has_media'),
                msg.get('image_path'),
                msg.get('views', 0),
                msg.get('forwards', 0)
            ))
        
        # Execute batch insert
        execute_batch(cur, insert_query, data_to_insert)
        conn.commit()
        
        logger.info(f"Successfully loaded {len(data_to_insert)} messages to PostgreSQL")
        cur.close()
        
    except Exception as e:
        logger.error(f"Error loading messages to database: {e}")
        conn.rollback()
        raise


def main():
    """Main entry point."""
    logger.info("Starting data load to PostgreSQL")
    
    # Read JSON files
    messages = read_json_files()
    
    if not messages:
        logger.warning("No messages found in data lake. Exiting.")
        return
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Create schema and table
        create_raw_schema(conn)
        
        # Load messages
        load_messages_to_db(conn, messages)
        
        logger.info("Data load completed successfully")
        
    finally:
        conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()
