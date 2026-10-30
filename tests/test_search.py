"""
test_search.py
--------------
Tests for the student search command (src/search.py).
Run with: pytest tests/ -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from extract import load_local_sample, load_local_outages
from transform import transform_all
from transform_outages import transform_outages, add_outage_info
from search import build_query, search


def sample_listings():
    listings = transform_all(load_local_sample())
    return add_outage_info(listings, transform_outages(load_local_outages()))


class TestBuildQuery:

    def test_no_options_has_no_where_part(self):
        sql, values = build_query()
        assert "WHERE" not in sql
        assert values == []

    def test_options_are_added_with_and(self):
        sql, values = build_query(max_rent=5000, nsfas=True)
        assert "monthly_rent_zar < ?" in sql
        assert "is_nsfas_accredited = 1" in sql
        assert " AND " in sql
        assert values == [5000]


class TestSearch:

    def test_no_options_returns_all_six_places(self):
        assert len(search(sample_listings())) == 6

    def test_max_rent_5000_returns_five_places_cheapest_first(self):
        result = search(sample_listings(), max_rent=5000)
        assert len(result) == 5
        assert result.iloc[0]["suburb"] == "Arcadia"

    def test_avoid_high_risk_leaves_out_sunnyside_and_braamfontein(self):
        result = search(sample_listings(), avoid_high_risk=True)
        assert len(result) == 4
        assert "Sunnyside" not in set(result["suburb"])

    def test_backup_under_5000_finds_hatfield_and_braamfontein(self):
        result = search(sample_listings(), max_rent=5000, backup=True)
        assert set(result["suburb"]) == {"Hatfield", "Braamfontein"}

    def test_results_include_contact_details(self):
        result = search(sample_listings(), max_rent=5000)
        assert "contact_email" in result.columns
        assert "listing_url" in result.columns
