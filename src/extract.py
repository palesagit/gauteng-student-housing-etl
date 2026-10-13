import os
import json
import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mandatory fields that every raw listing record must contain
REQUIRED_FIELDS: set[str] = {"listing_id", "title", "suburb"}

SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw_listings_sample.json"
)


def validate_raw_records(records: list[dict]) -> list[dict]:
    """
    Filter out records that are missing mandatory fields.

    Args:
        records (list[dict]): Raw listing records from any source.

    Returns:
        list[dict]: Only records that contain all REQUIRED_FIELDS.
    """
    valid, dropped = [], 0
    for rec in records:
        if REQUIRED_FIELDS.issubset(rec.keys()):
            valid.append(rec)
        else:
            missing = REQUIRED_FIELDS - rec.keys()
            logger.warning(f"⚠️  Dropping record — missing fields {missing}: {rec}")
            dropped += 1
    if dropped:
        logger.warning(f"⚠️  {dropped} record(s) dropped due to missing required fields.")
    return valid


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    reraise=False,
)
def _call_api(endpoint_url: str) -> list[dict]:
    """
    Internal helper that performs the HTTP GET with tenacity retry.
    Raises on non-2xx status or network errors (so tenacity can retry).

    Args:
        endpoint_url (str): Remote API URL.

    Returns:
        list[dict]: Parsed JSON response as a list of dicts.
    """
    response = requests.get(endpoint_url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_from_api(endpoint_url: str) -> list[dict]:
    """
    Fetch live JSON accommodation listings from a remote API endpoint.
    Retries up to 3 times with exponential back-off on network errors.

    Args:
        endpoint_url (str): Remote API URL.

    Returns:
        list[dict]: Validated raw listing dictionaries.
    """
    try:
        data = _call_api(endpoint_url)
        logger.info(f"✅ Successfully fetched live listings from {endpoint_url}")
        return validate_raw_records(data)
    except Exception as e:
        logger.error(f"❌ API fetch failed after retries: {e}. Falling back to local dataset.")
        return load_local_sample()