# gauteng-student-housing-etl
My Data Engineering project: an ETL pipeline for student accommodation in Gauteng (UP, Wits, UJ and TUT), built with Python, pandas, SQL and PostgreSQL.

## Why I built this
When I looked at student accommodation listings, I noticed how hard they are to compare. Rent is written as "R3500pm" or
"R 4,800 / month", NSFAS status is just free text, and the amenities are loose phrases. On top of that, loadshedding and water
outages are a daily problem in Gauteng, and a cheap room is not a good deal if the suburb is without power or water for
many hours.

I built this project to make it easier for students to find accommodation that fits their specific needs, without spending
hours checking listings across many different websites.

So I built a pipeline that cleans the listings, adds loadshedding and water outage information for each suburb, and puts everything
in one table. A student can then search it with SQL, for example "under R5000, NSFAS accredited, close to campus and not a high
outage risk suburb", and every result shows who to contact.

> **Important:** the data in the `data/` folder is **sample data that I made up for learning**. It is not real listings and it
> is not real Eskom or municipal schedules.

## What I used to learn this
Before starting the project I completed two courses:
- the IBM Data Engineering skills course on IBM SkillsBuild
- *IBM Data Engineering Basics for Everyone* on edX

The project follows the ETL idea from those courses: Extract, Transform, Load.

## How it works
```
data/*.json  ->  extract.py  ->  transform.py + transform_outages.py  ->  load.py  ->  SQL searches
(raw, messy)     (read, check)   (clean, add outage risk)                (CSV / PostgreSQL)
```

| Step | File | What it does |
|---|---|---|
| Extract | `src/extract.py` | Reads the listings and outages (from my sample files, or an API) and drops records with missing fields |
| Transform | `src/transform.py` | Cleans listings: rent becomes a number, NSFAS becomes True/False, and I flag WiFi, backup power and backup water. It keeps the address and contact details |
| Transform | `src/transform_outages.py` | Cleans outages, matches them to listings by suburb, adds outage counts and hours, and gives each listing a High / Medium / Low risk. It warns me if a suburb name does not match |
| Load | `src/load.py` | Saves the results to CSV files or PostgreSQL tables |
| Run all | `src/pipeline.py` | Runs extract, transform and load in order |
| Search | `src/search.py` | A search command for students. It builds a SQL query from the options you choose and runs it |
| Search | `sql/student_queries.sql` | 7 ready-made SQL searches |

I decided on the outage risk like this: **High** = 12 hours or more of outages in the suburb, **Medium** = 4 hours or more,
otherwise **Low**. You can change these two numbers in `src/transform_outages.py`.

## Project layout
```
data/          sample input files (listings and outages, JSON)
src/           the pipeline code (extract, transform, load, search)
sql/           example SQL searches for students
tests/         automatic tests (see tests/TEST_GUIDE.md)
output/        CSV files made by the pipeline (not committed to git)
```

## Setup
You need Python 3.10 or newer. Docker is only needed if you want to use PostgreSQL.
```bash
pip install -r requirements.txt
cp .env.example .env
```
(On Windows PowerShell use `copy .env.example .env`.)

## Quick start
```bash
python src/pipeline.py                       # clean the data and make the CSV files
python src/search.py --max-rent 5000         # search for places under R5000
pytest tests/ -v                             # run all the tests
```

## Demo: see it working
Run these in order.

### 1. Run the tests
```bash
pytest tests/ -v
```
You should see **46 passed**.

### 2. Run the pipeline
```bash
python src/pipeline.py
```
You should see a warning that one record was dropped (`BAD-001`, which has no suburb on purpose), then:
```
Saved 7 rows to output/outages.csv
Saved 6 rows to output/listings_with_outages.csv
Pipeline finished
```

### 3. Look at the cleaned data
```bash
python -c "import pandas as pd; print(pd.read_csv('output/listings_with_outages.csv')[['title','suburb','monthly_rent_zar','outage_hours','outage_risk']].to_string())"
```
Rents are now numbers and every listing has an outage risk. Braamfontein and Sunnyside are **High**, Hillcrest is **Low**.

### 4. Search as a student (no database needed)
`src/search.py` reads `output/listings_with_outages.csv`, puts it in a small temporary SQL database, builds a SQL query from the
options you choose, runs it and prints the matches. Run the pipeline first.
```bash
python src/search.py --max-rent 5000
python src/search.py --max-rent 5000 --nsfas --wifi --max-distance 1 --avoid-high-risk
python src/search.py --max-rent 5000 --backup
```
| Option | Meaning |
|---|---|
| `--max-rent 5000` | rent under R5000 a month |
| `--max-distance 1` | within 1 km of campus |
| `--nsfas` | NSFAS accredited only |
| `--wifi` | must have WiFi (or fibre) |
| `--backup` | must have backup power or backup water |
| `--avoid-high-risk` | skip suburbs with High outage risk |

Results: the first command finds **5** places, the second finds **3** (Arcadia, Auckland Park, Hatfield), and the third finds **2** (Hatfield and Braamfontein).

### 5. Start PostgreSQL and load the data
```bash
docker compose up -d
docker ps
python src/pipeline.py --to-postgres
```
`docker ps` should show the `housing-db` container running. The pipeline log should end with the tables being loaded.

### 6. Run SQL queries in PostgreSQL
Open a SQL prompt inside the database:
```bash
docker exec -it housing-db psql -U housing_user -d gauteng_housing_db
```
Then type or paste these (leave the prompt with `\q`).

See the tables:
```sql
\dt
```
Query 1: everything under R5000, cheapest first
```sql
SELECT title, suburb, monthly_rent_zar, contact_email FROM listings_with_outages WHERE monthly_rent_zar < 5000 ORDER BY monthly_rent_zar;
```
Query 6: budget, NSFAS, WiFi, close to campus and not a high outage risk, all together
```sql
SELECT title, suburb, monthly_rent_zar, outage_risk, address, contact_email FROM listings_with_outages WHERE monthly_rent_zar < 5000 AND is_nsfas_accredited = TRUE AND has_wifi = TRUE AND distance_to_campus_km <= 1 AND outage_risk <> 'High' ORDER BY monthly_rent_zar;
```
Query 7: how many places in each risk level, and the average rent
```sql
SELECT outage_risk, COUNT(*) AS places, ROUND(AVG(monthly_rent_zar)) AS average_rent FROM listings_with_outages GROUP BY outage_risk ORDER BY places DESC;
```
Join the two tables to see exactly which outages affect the cheaper places
```sql
SELECT l.title, o.outage_type, o.start_time, o.duration_hours FROM listings_with_outages l JOIN outages o ON LOWER(l.suburb) = LOWER(o.suburb) WHERE l.monthly_rent_zar < 5000 ORDER BY o.start_time;
```
Expected: Query 1 returns 5 rows, Query 6 returns Arcadia, Auckland Park and Hatfield, Query 7 shows Medium 3, High 2, Low 1, and the join returns 7 outages.

To run all 7 searches from the file at once:
```bash
# Mac / Linux
docker exec -i housing-db psql -U housing_user -d gauteng_housing_db < sql/student_queries.sql
# Windows PowerShell
Get-Content sql/student_queries.sql | docker exec -i housing-db psql -U housing_user -d gauteng_housing_db
```
You can also connect a SQL tool such as DBeaver or pgAdmin using host `localhost`, port `5432` and the user, password and database from your `.env`.
Change the numbers (like 5000) to match your own budget. Stop the database with `docker compose down`.

### 7. What happens when an outage API is down (optional)
```bash
# Mac / Linux
OUTAGES_API_URL=http://localhost:9/outages python src/pipeline.py
# Windows PowerShell
$env:OUTAGES_API_URL="http://localhost:9/outages"; python src/pipeline.py
```
The pipeline logs that the API fetch failed, falls back to my sample file, and still finishes. (In PowerShell, run `Remove-Item Env:OUTAGES_API_URL` afterwards.)

## Run the tests
```bash
pytest tests/ -v                                   # all tests
pytest tests/test_search.py -v                     # one file
pytest tests/ --cov=src --cov-report=term-missing  # with a coverage report
```
There are 46 tests. They cover cleaning rent, NSFAS and amenities, cleaning outages, matching suburbs, the risk levels,
loading into a database, all 7 SQL searches, and the search command. See [`tests/TEST_GUIDE.md`](tests/TEST_GUIDE.md) for more.

## Tables and columns
**`listings_with_outages`** (one row per listing):
`listing_id`, `title`, `university`, `suburb`, `city`, `room_type`, `address`, `contact_email`, `listing_url`,
`monthly_rent_zar`, `deposit_zar`, `is_nsfas_accredited`, `distance_to_campus_km`, `has_wifi`, `has_backup_power`,
`has_backup_water`, `power_outages`, `water_outages`, `outage_hours`, `outage_risk`

**`outages`** (one row per outage):
`outage_id`, `outage_type` (loadshedding or water), `suburb`, `city`, `loadshedding_stage`, `start_time`, `duration_hours`, `reason`

## Using live outage data
If you have a JSON outages API, put its URL in `OUTAGES_API_URL` in your `.env`. The records must use the same field names as
`data/outages_sample.json`. If the API fails, the pipeline falls back to my sample file.

## Troubleshooting
| Problem | Fix |
|---|---|
| `search.py` says the CSV file is not found | Run `python src/pipeline.py` first |
| Warning about `BAD-001` | This is normal. That sample record has no suburb on purpose, to show that validation works |
| Warning "Outage suburbs with no matching listing" | A suburb name is spelled differently in the outage data. Fix the spelling |
| `--to-postgres` gives a connection error | Start the database with `docker compose up -d` and check the values in `.env` |
| `psql` or `docker` not found | Install Docker Desktop, or use step 4 (`search.py`), which needs no database |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |

## Limitations
- I only used sample data: 6 listings and 7 valid outages, all made up (the outage dates are examples). One additional invalid sample outage is dropped because it has no suburb.
- Outages are matched to listings by suburb name only.
- Each `--to-postgres` run replaces the tables, so no history is kept.
- Nothing runs on a schedule yet.

## What I want to add next
- Real listings and a real outage source
- Schedule the pipeline with Airflow
- Keep a history of each run

-----------------------------------------------
WTC-GLMUMAUR
