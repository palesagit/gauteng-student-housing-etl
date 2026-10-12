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


