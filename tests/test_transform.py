"""
test_transform.py
-----------------
Unit tests for Gauteng Student Accommodation transformation logic.
Run with: pytest tests/ -v
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from transform import (
    clean_currency,
    parse_nsfas_status,
    has_amenity,
    transform_listing,
    transform_all,
)


class TestCurrencyCleaning:

    def test_clean_currency_parses_standard_rand_string(self):
        assert clean_currency("R 4,800 / month") == 4800.0

    def test_clean_currency_parses_compact_rand_string(self):
        assert clean_currency("R3500pm") == 3500.0

    def test_clean_currency_handles_numeric_input(self):
        assert clean_currency(6200) == 6200.0

    def test_clean_currency_handles_none_input(self):
        assert clean_currency(None) is None


class TestNsfasParsing:

    def test_parse_nsfas_status_approved_string_returns_true(self):
        assert parse_nsfas_status("YES - Approved") is True

    def test_parse_nsfas_status_accredited_string_returns_true(self):
        assert parse_nsfas_status("Accredited") is True

    def test_parse_nsfas_status_no_string_returns_false(self):
        assert parse_nsfas_status("NO") is False

    def test_parse_nsfas_status_none_input_returns_false(self):
        assert parse_nsfas_status(None) is False
    
class TestAmenityParsing:

    def test_has_amenity_detects_wifi_keyword(self):
        amenities = ["Free High-Speed WiFi", "Generator Backup Power"]
        assert has_amenity(amenities, "wifi") is True

    def test_has_amenity_detects_backup_power_keyword(self):
        amenities = ["Solar Power Backup", "Biometric Access"]
        assert has_amenity(amenities, "solar") is True

    def test_has_amenity_returns_false_when_absent(self):
        amenities = ["Laundry"]
        assert has_amenity(amenities, "generator") is False


class TestListingTransformation:

    def test_transform_listing_valid_raw_record(self):
        raw = {
            "listing_id": "RES-TEST-01",
            "title": "TuksRes Hatfield House",
            "university_partner": "University of Pretoria",
            "suburb": "Hatfield",
            "city": "Pretoria",
            "monthly_rent_raw": "R 4,500",
            "nsfas_accredited_raw": "YES",
            "amenities": ["Uncapped WiFi", "Generator Backup"],
        }
        res = transform_listing(raw)
        assert res is not None
        assert res["listing_id"] == "RES-TEST-01"
        assert res["monthly_rent_zar"] == 4500.0
        assert res["is_nsfas_accredited"] is True
        assert res["has_wifi"] is True
        assert res["has_backup_power"] is True

    def test_transform_all_returns_pandas_dataframe(self):
        raw = [{
            "listing_id": "RES-TEST-02",
            "title": "Sunnyside Digs",
            "suburb": "Sunnyside",
            "monthly_rent_raw": "R 3,200",
        }]
        df = transform_all(raw)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1



