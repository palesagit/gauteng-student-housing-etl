"""
load.py
-------
LOAD step: save the clean data to a CSV file or a PostgreSQL table.
"""

import os
import logging
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # reads the .env file (see .env.example)
logger = logging.getLogger(__name__)


def save_to_csv(df: pd.DataFrame, path: str = "output/listings_with_outages.csv") -> str:
    """Save the DataFrame as a CSV file and return the path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"✅ Saved {len(df)} rows to {path}")
    return path


def get_postgres_engine():
    """Build a database connection from the values in .env."""
    url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)


def load_to_postgres(df: pd.DataFrame, table_name: str, engine=None) -> None:
    """Write the DataFrame to a database table (replaces the old table)."""
    engine = engine or get_postgres_engine()
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    logger.info(f"✅ Loaded {len(df)} rows into table '{table_name}'")
