"""
test_queries.py
---------------
Checks that the student SQL searches in sql/student_queries.sql work
and give the right answers on the sample data.
Run with: pytest tests/ -v
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from extract import load_local_sample, load_local_outages
from transform import transform_all
from transform_outages import transform_outages, add_outage_info
from load import load_to_postgres

SQL_FILE = os.path.join(os.path.dirname(__file__), "..", "sql", "student_queries.sql")


def build_test_database():
    """Run extract + transform and put the result in a small test database."""
    listings = transform_all(load_local_sample())
    final = add_outage_info(listings, transform_outages(load_local_outages()))
    engine = create_engine("sqlite:///:memory:")
    load_to_postgres(final, "listings_with_outages", engine=engine)
    return engine


def read_queries():
    """Split the .sql file into separate queries (ignores comment lines)."""
    with open(SQL_FILE, encoding="utf-8") as f:
        lines = [line for line in f if not line.strip().startswith("--")]
    return [q.strip() for q in "".join(lines).split(";") if q.strip()]


class TestStudentQueries:

    def test_file_has_seven_queries(self):
        assert len(read_queries()) == 7

    def test_budget_query_returns_only_rents_under_5000(self):
        result = pd.read_sql(read_queries()[0], build_test_database())
        assert len(result) == 5
        assert (result["monthly_rent_zar"] < 5000).all()

    def test_nsfas_query_returns_five_places(self):
        assert len(pd.read_sql(read_queries()[1], build_test_database())) == 5

    def test_walkable_query_returns_four_places(self):
        assert len(pd.read_sql(read_queries()[2], build_test_database())) == 4

    def test_backup_query_finds_hatfield_and_braamfontein(self):
        result = pd.read_sql(read_queries()[3], build_test_database())
        assert set(result["suburb"]) == {"Hatfield", "Braamfontein"}

    def test_low_outage_query_leaves_out_high_risk_suburbs(self):
        result = pd.read_sql(read_queries()[4], build_test_database())
        assert "High" not in set(result["outage_risk"])

    def test_combined_query_finds_three_places(self):
        result = pd.read_sql(read_queries()[5], build_test_database())
        assert set(result["suburb"]) == {"Hatfield", "Auckland Park", "Arcadia"}

    def test_summary_query_counts_all_six_places(self):
        result = pd.read_sql(read_queries()[6], build_test_database())
        assert result["places"].sum() == 6


class TestContactDetails:

    def test_every_search_shows_contact_details(self):
        for query in read_queries()[:6]:
            result = pd.read_sql(query, build_test_database())
            assert "contact_email" in result.columns
            assert "listing_url" in result.columns

    def test_contact_email_is_correct_for_hatfield(self):
        result = pd.read_sql(read_queries()[0], build_test_database())
        hatfield = result[result["suburb"] == "Hatfield"].iloc[0]
        assert hatfield["contact_email"] == "info@hatfieldres.co.za"


class TestWifiFlag:

    def test_fiber_counts_as_wifi(self):
        df = transform_all(load_local_sample())
        hillcrest = df[df["suburb"] == "Hillcrest"].iloc[0]
        assert hillcrest["has_wifi"] == True  # Hillcrest has "High-Speed Fiber"
