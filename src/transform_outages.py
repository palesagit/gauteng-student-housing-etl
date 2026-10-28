"""
transform_outages.py
--------------------
TRANSFORM step for current affairs data: loadshedding (power)
and water outages. Also joins the outages onto the listings.
"""

import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# Total outage hours at or above these numbers set the risk level
HIGH_RISK_HOURS = 12
MEDIUM_RISK_HOURS = 4


def parse_outage_type(value) -> str:
    """Turn 'Load shedding' / 'Water outage' into 'loadshedding' / 'water'."""
    text = str(value).lower()
    if "load" in text or "power" in text:
        return "loadshedding"
    if "water" in text:
        return "water"
    return "other"


def parse_stage(value):
    """Turn 'Stage 4' into 4. Returns None if there is no stage."""
    match = re.search(r"\d+", str(value)) if value else None
    return int(match.group()) if match else None


def parse_duration_hours(value):
    """Turn '4 hours', '2.5 hours' or '4 hrs' into a float like 4.0."""
    match = re.search(r"\d+\.?\d*", str(value)) if value else None
    return float(match.group()) if match else None


def transform_outage(raw: dict) -> dict:
    """Clean one raw outage record."""
    return {
        "outage_id": raw["outage_id"],
        "outage_type": parse_outage_type(raw["outage_type_raw"]),
        "suburb": raw["suburb"].strip(),
        "city": raw.get("city"),
        "loadshedding_stage": parse_stage(raw.get("stage_raw")),
        "start_time": raw.get("start_time"),
        "duration_hours": parse_duration_hours(raw.get("duration_raw")),
        "reason": raw.get("reason"),
    }


def transform_outages(raw_records: list[dict]) -> pd.DataFrame:
    """Clean every outage record and return a DataFrame."""
    return pd.DataFrame([transform_outage(r) for r in raw_records])


def risk_level(total_hours: float) -> str:
    """Turn total outage hours into 'High', 'Medium' or 'Low'."""
    if total_hours >= HIGH_RISK_HOURS:
        return "High"
    if total_hours >= MEDIUM_RISK_HOURS:
        return "Medium"
    return "Low"


def add_outage_info(listings: pd.DataFrame, outages: pd.DataFrame) -> pd.DataFrame:
    """
    Add outage columns to each listing, matched by suburb:
    power_outages, water_outages, outage_hours and outage_risk.
    """
    result = listings.copy()
    result["suburb_key"] = result["suburb"].str.lower()  # so 'Hatfield' == 'hatfield'

    summary = pd.DataFrame(columns=["suburb_key", "power_outages", "water_outages", "outage_hours"])
    if not outages.empty:
        o = outages.copy()
        o["suburb_key"] = o["suburb"].str.lower()
        summary = o.groupby("suburb_key").agg(
            power_outages=("outage_type", lambda t: (t == "loadshedding").sum()),
            water_outages=("outage_type", lambda t: (t == "water").sum()),
            outage_hours=("duration_hours", "sum"),
        ).reset_index()

    result = result.merge(summary, on="suburb_key", how="left")
    for col in ["power_outages", "water_outages", "outage_hours"]:
        result[col] = result[col].fillna(0)
    result[["power_outages", "water_outages"]] = result[["power_outages", "water_outages"]].astype(int)
    result["outage_risk"] = result["outage_hours"].apply(risk_level)
    return result.drop(columns="suburb_key")
