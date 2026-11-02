-- overall
SELECT COUNT(*) AS n, SUM(DEFAULT_FLAG) AS defaults, ROUND(100.0*AVG(DEFAULT_FLAG),2) AS default_rate_pct
FROM clients;

-- by_age_band
SELECT CASE WHEN AGE<25 THEN '1. <25' WHEN AGE<35 THEN '2. 25-34'
            WHEN AGE<45 THEN '3. 35-44' WHEN AGE<55 THEN '4. 45-54' ELSE '5. 55+' END AS age_band,
       COUNT(*) AS n, ROUND(100.0*AVG(DEFAULT_FLAG),2) AS default_rate_pct
FROM clients GROUP BY age_band ORDER BY age_band;

-- by_limit_band
SELECT CASE WHEN LIMIT_BAL<50000 THEN '1. <50k' WHEN LIMIT_BAL<100000 THEN '2. 50-100k'
            WHEN LIMIT_BAL<200000 THEN '3. 100-200k' WHEN LIMIT_BAL<400000 THEN '4. 200-400k'
            ELSE '5. 400k+' END AS limit_band,
       COUNT(*) AS n, ROUND(100.0*AVG(DEFAULT_FLAG),2) AS default_rate_pct
FROM clients GROUP BY limit_band ORDER BY limit_band;

-- by_education
SELECT CASE EDUCATION WHEN 1 THEN 'Graduate school' WHEN 2 THEN 'University'
            WHEN 3 THEN 'High school' ELSE 'Other' END AS education,
       COUNT(*) AS n, ROUND(100.0*AVG(DEFAULT_FLAG),2) AS default_rate_pct
FROM clients GROUP BY EDUCATION ORDER BY default_rate_pct DESC;

-- by_late_payment_count
WITH t AS (
  SELECT DEFAULT_FLAG,
         (PAY_1>0)+(PAY_2>0)+(PAY_3>0)+(PAY_4>0)+(PAY_5>0)+(PAY_6>0) AS late_months
  FROM clients)
SELECT late_months, COUNT(*) AS n, ROUND(100.0*AVG(DEFAULT_FLAG),2) AS default_rate_pct
FROM t GROUP BY late_months ORDER BY late_months;

-- by_latest_payment_status
SELECT PAY_1 AS latest_status, COUNT(*) AS n, ROUND(100.0*AVG(DEFAULT_FLAG),2) AS default_rate_pct
FROM clients GROUP BY PAY_1 ORDER BY PAY_1;

-- highest_risk_segments
WITH seg AS (
  SELECT CASE WHEN LIMIT_BAL<100000 THEN 'low limit' WHEN LIMIT_BAL<250000 THEN 'mid limit' ELSE 'high limit' END AS limit_seg,
         CASE WHEN PAY_1<=0 THEN 'on time' WHEN PAY_1=1 THEN '1m late' ELSE '2m+ late' END AS latest_status,
         CASE WHEN AGE<30 THEN 'under 30' ELSE '30+' END AS age_seg,
         DEFAULT_FLAG
  FROM clients)
SELECT limit_seg, latest_status, age_seg, COUNT(*) AS n,
       ROUND(100.0*AVG(DEFAULT_FLAG),2) AS default_rate_pct,
       RANK() OVER (ORDER BY AVG(DEFAULT_FLAG) DESC) AS risk_rank
FROM seg GROUP BY limit_seg, latest_status, age_seg
HAVING COUNT(*) >= 200
ORDER BY risk_rank LIMIT 10;

