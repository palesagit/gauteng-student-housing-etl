"""
test_outages.py
---------------
Unit tests for the loadshedding and water outage part of the pipeline.
Run with: pytest tests/ -v
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from extract import load_local_outages, validate_raw_records, REQUIRED_OUTAGE_FIELDS
from transform import transform_all
from transform_outages import (
    parse_outage_type,
    parse_stage,
    parse_duration_hours,
    transform_outages,
    risk_level,
    add_outage_info,
    suburb_key,
    find_unmatched_suburbs,
)
from load import load_to_postgres


class TestOutageParsing:

    def test_parse_outage_type_loadshedding(self):
        assert parse_outage_type("Load shedding") == "loadshedding"

    def test_parse_outage_type_water(self):
        assert parse_outage_type("Water outage") == "water"

    def test_parse_stage_reads_number(self):
        assert parse_stage("Stage 4") == 4

    def test_parse_stage_none_returns_none(self):
        assert parse_stage(None) is None

    def test_parse_duration_hours_variations(self):
        assert parse_duration_hours("4 hours") == 4.0
        assert parse_duration_hours("2.5 hours") == 2.5
        assert parse_duration_hours("4 hrs") == 4.0


class TestOutageExtract:

    def test_validation_drops_record_without_suburb(self):
        records = [
            {"outage_id": "A", "outage_type_raw": "Water", "suburb": "Hatfield"},
            {"outage_id": "B", "outage_type_raw": "Water"},
        ]
        assert len(validate_raw_records(records, REQUIRED_OUTAGE_FIELDS)) == 1

    def test_load_local_outages_skips_the_bad_sample_record(self):
        ids = [r["outage_id"] for r in load_local_outages()]
        assert "BAD-001" not in ids
        assert len(ids) == 7


class TestOutageJoin:

    def test_risk_level_thresholds(self):
        assert risk_level(0) == "Low"
        assert risk_level(5) == "Medium"
        assert risk_level(20) == "High"

    def test_add_outage_info_counts_by_suburb(self):
        listings = pd.DataFrame([
            {"listing_id": "1", "suburb": "Hatfield"},
            {"listing_id": "2", "suburb": "Hillcrest"},
        ])
        outages = transform_outages(load_local_outages())
        result = add_outage_info(listings, outages)
        hatfield = result[result["suburb"] == "Hatfield"].iloc[0]
        assert hatfield["power_outages"] == 1
        assert hatfield["water_outages"] == 1
        assert hatfield["outage_risk"] == "Medium"

    def test_suburb_with_no_outages_is_low_risk(self):
        listings = pd.DataFrame([{"listing_id": "2", "suburb": "Hillcrest"}])
        result = add_outage_info(listings, transform_outages(load_local_outages()))
        assert result.iloc[0]["outage_risk"] == "Low"
        assert result.iloc[0]["outage_hours"] == 0


class TestSuburbMatching:

    def test_suburb_key_ignores_case_and_extra_spaces(self):
        names = pd.Series(["  Auckland   Park ", "HATFIELD"])
        assert list(suburb_key(names)) == ["auckland park", "hatfield"]

    def test_misspelled_outage_suburb_is_reported(self):
        listings = pd.DataFrame([{"suburb": "Hatfield"}])
        outages = pd.DataFrame([{"suburb": "Hatfeld", "outage_type": "water", "duration_hours": 3.0}])
        assert find_unmatched_suburbs(listings, outages) == ["Hatfeld"]

    def test_matching_suburbs_are_not_reported(self):
        listings = pd.DataFrame([{"suburb": "Hatfield"}])
        outages = pd.DataFrame([{"suburb": "hatfield ", "outage_type": "water", "duration_hours": 3.0}])
        assert find_unmatched_suburbs(listings, outages) == []

    def test_extra_spaces_still_count_the_outage(self):
        listings = pd.DataFrame([{"suburb": "Auckland Park"}])
        outages = pd.DataFrame([{"suburb": "Auckland  Park", "outage_type": "water", "duration_hours": 5.0}])
        result = add_outage_info(listings, outages)
        assert result.iloc[0]["water_outages"] == 1


class TestLoad:

    def test_load_writes_rows_to_a_database(self):
        engine = create_engine("sqlite:///:memory:")  # tiny test database
        df = pd.DataFrame([{"suburb": "Hatfield", "outage_risk": "Medium"}])
        load_to_postgres(df, "test_table", engine=engine)
        assert len(pd.read_sql("SELECT * FROM test_table", engine)) == 1
