"""
pipeline.py
-----------
Runs the whole ETL: Extract -> Transform -> Load.

    python src/pipeline.py                # saves CSV files in output/
    python src/pipeline.py --to-postgres  # also loads into PostgreSQL
"""

import os
import sys
import logging
from dotenv import load_dotenv

from extract import load_local_sample, load_local_outages, fetch_outages_from_api
from transform import transform_all
from transform_outages import transform_outages, add_outage_info
from load import save_to_csv, load_to_postgres

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(to_postgres: bool = False):
    # 1. EXTRACT
    raw_listings = load_local_sample()
    api_url = os.getenv("OUTAGES_API_URL")
    raw_outages = fetch_outages_from_api(api_url) if api_url else load_local_outages()

    # 2. TRANSFORM
    listings = transform_all(raw_listings)
    outages = transform_outages(raw_outages)
    final = add_outage_info(listings, outages)

    # 3. LOAD
    save_to_csv(outages, "output/outages.csv")
    save_to_csv(final, "output/listings_with_outages.csv")
    if to_postgres:
        load_to_postgres(outages, "outages")
        load_to_postgres(final, "listings_with_outages")

    logger.info("🎉 Pipeline finished")
    return final


if __name__ == "__main__":
    run(to_postgres="--to-postgres" in sys.argv)
