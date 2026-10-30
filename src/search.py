"""
search.py
---------
A simple search for students. It reads the pipeline's output file, puts it in a
small SQL database and runs a SQL search built from your options.

Examples (run `python src/pipeline.py` first):
    python src/search.py --max-rent 5000
    python src/search.py --max-rent 5000 --nsfas --wifi --max-distance 1
    python src/search.py --max-rent 5000 --backup --avoid-high-risk
"""

import sqlite3
import argparse
import pandas as pd

CSV_PATH = "output/listings_with_outages.csv"
COLUMNS = ("title, suburb, monthly_rent_zar, distance_to_campus_km, outage_risk, "
           "contact_email, listing_url")


def build_query(max_rent=None, nsfas=False, wifi=False, backup=False,
                max_distance=None, avoid_high_risk=False):
    """Build a SQL query and its values from the chosen options."""
    conditions, values = [], []
    if max_rent is not None:
        conditions.append("monthly_rent_zar < ?")
        values.append(max_rent)
    if nsfas:
        conditions.append("is_nsfas_accredited = 1")
    if wifi:
        conditions.append("has_wifi = 1")
    if backup:
        conditions.append("(has_backup_power = 1 OR has_backup_water = 1)")
    if max_distance is not None:
        conditions.append("distance_to_campus_km <= ?")
        values.append(max_distance)
    if avoid_high_risk:
        conditions.append("outage_risk <> 'High'")

    sql = f"SELECT {COLUMNS} FROM listings_with_outages"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    return sql + " ORDER BY monthly_rent_zar", values


def search(listings: pd.DataFrame, **options) -> pd.DataFrame:
    """Run the search on a DataFrame of listings and return the matches."""
    connection = sqlite3.connect(":memory:")
    listings.to_sql("listings_with_outages", connection, index=False)
    sql, values = build_query(**options)
    result = pd.read_sql(sql, connection, params=values)
    connection.close()
    return result


def main():
    parser = argparse.ArgumentParser(description="Search student accommodation.")
    parser.add_argument("--max-rent", type=float, help="most you can pay per month (R)")
    parser.add_argument("--max-distance", type=float, help="furthest from campus (km)")
    parser.add_argument("--nsfas", action="store_true", help="NSFAS accredited only")
    parser.add_argument("--wifi", action="store_true", help="must have WiFi")
    parser.add_argument("--backup", action="store_true", help="must have backup power or water")
    parser.add_argument("--avoid-high-risk", action="store_true", help="skip High outage risk suburbs")
    args = parser.parse_args()

    listings = pd.read_csv(CSV_PATH)
    result = search(
        listings, max_rent=args.max_rent, nsfas=args.nsfas, wifi=args.wifi,
        backup=args.backup, max_distance=args.max_distance,
        avoid_high_risk=args.avoid_high_risk,
    )
    print(f"{len(result)} place(s) found")
    if not result.empty:
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
