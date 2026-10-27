-- student_queries.sql
-- Example searches for students. Run them on the table made by the pipeline:
--   listings_with_outages   (load it with: python src/pipeline.py --to-postgres)
-- Change the numbers (like 5000) to match your own budget.
-- Each query ends with a semicolon.

-- Query 1: Everything under R5000 a month, cheapest first
SELECT title, suburb, monthly_rent_zar
FROM listings_with_outages
WHERE monthly_rent_zar < 5000
ORDER BY monthly_rent_zar;

-- Query 2: Under R5000 and NSFAS accredited
SELECT title, suburb, monthly_rent_zar
FROM listings_with_outages
WHERE monthly_rent_zar < 5000
  AND is_nsfas_accredited = TRUE
ORDER BY monthly_rent_zar;

-- Query 3: Under R5000 and within 1 km of campus (walkable)
SELECT title, suburb, monthly_rent_zar, distance_to_campus_km
FROM listings_with_outages
WHERE monthly_rent_zar < 5000
  AND distance_to_campus_km <= 1
ORDER BY distance_to_campus_km;

-- Query 4: Under R5000 with backup power or backup water
SELECT title, suburb, monthly_rent_zar, has_backup_power, has_backup_water
FROM listings_with_outages
WHERE monthly_rent_zar < 5000
  AND (has_backup_power = TRUE OR has_backup_water = TRUE);

-- Query 5: Under R5000 in a suburb that is NOT high outage risk
SELECT title, suburb, monthly_rent_zar, outage_risk, outage_hours
FROM listings_with_outages
WHERE monthly_rent_zar < 5000
  AND outage_risk <> 'High'
ORDER BY outage_hours;

-- Query 6: Everything together: budget, NSFAS, WiFi, walkable, not high outage risk
SELECT title, suburb, monthly_rent_zar, outage_risk
FROM listings_with_outages
WHERE monthly_rent_zar < 5000
  AND is_nsfas_accredited = TRUE
  AND has_wifi = TRUE
  AND distance_to_campus_km <= 1
  AND outage_risk <> 'High'
ORDER BY monthly_rent_zar;

-- Query 7: How many places are in each outage risk level, and the average rent?
SELECT outage_risk,
       COUNT(*) AS places,
       ROUND(AVG(monthly_rent_zar)) AS average_rent
FROM listings_with_outages
GROUP BY outage_risk
ORDER BY places DESC;
