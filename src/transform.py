"""
transform.py
------------
TRANSFORM step for student housing listings:
turns messy raw text (like "R 4,800 / month") into clean values.
"""

import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# Keywords that mean "this place has internet"
WIFI_WORDS = ["wifi", "wi-fi", "fiber", "fibre"]

# Keywords that mean "this place keeps the power / water on"
BACKUP_POWER_WORDS = ["generator", "solar", "inverter", "backup power"]
BACKUP_WATER_WORDS = ["water tank", "borehole", "jojo"]


def clean_currency(value):
    """Turn 'R 4,800 / month' (or 3500, or None) into a float like 4800.0."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"\d[\d,]*\.?\d*", str(value))
    if match is None:
        return None
    return float(match.group().replace(",", ""))


def parse_nsfas_status(value) -> bool:
    """Turn text like 'YES - Approved' or 'NO' into True / False."""
    if value is None:
        return False
    text = str(value).strip().lower()
    if text.startswith("no"):  # also catches "not accredited"
        return False
    return any(word in text for word in ["yes", "approved", "accredited"])


def has_amenity(amenities, keyword: str) -> bool:
    """Check if any amenity in the list contains the keyword (ignores case)."""
    if not amenities:
        return False
    return any(keyword.lower() in item.lower() for item in amenities)


def has_any_amenity(amenities, keywords: list[str]) -> bool:
    """Same as has_amenity, but True if ANY of the keywords is found."""
    return any(has_amenity(amenities, word) for word in keywords)


def transform_listing(raw: dict):
    """Clean one raw listing. Returns a dict, or None if the record is unusable."""
    if not raw.get("listing_id") or not raw.get("suburb"):
        logger.warning(f"⚠️  Skipping listing with no id or suburb: {raw}")
        return None
    amenities = raw.get("amenities")
    return {
        "listing_id": raw["listing_id"],
        "title": raw.get("title"),
        "university": raw.get("university_partner"),
        "suburb": raw["suburb"].strip(),
        "city": raw.get("city"),
        "room_type": raw.get("room_type"),
        "address": raw.get("address"),
        "contact_email": raw.get("contact_email"),
        "listing_url": raw.get("listing_url"),
        "monthly_rent_zar": clean_currency(raw.get("monthly_rent_raw")),
        "deposit_zar": clean_currency(raw.get("deposit_raw")),
        "is_nsfas_accredited": parse_nsfas_status(raw.get("nsfas_accredited_raw")),
        "distance_to_campus_km": raw.get("distance_to_campus_km"),
        "has_wifi": has_any_amenity(amenities, WIFI_WORDS),
        "has_backup_power": has_any_amenity(amenities, BACKUP_POWER_WORDS),
        "has_backup_water": has_any_amenity(amenities, BACKUP_WATER_WORDS),
    }


def transform_all(raw_records: list[dict]) -> pd.DataFrame:
    """Clean every listing and return them as a pandas DataFrame."""
    cleaned = [transform_listing(r) for r in raw_records]
    return pd.DataFrame([c for c in cleaned if c is not None])
