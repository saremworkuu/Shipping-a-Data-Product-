-- Dimension table for dates
-- This table contains date attributes for time-based analysis

WITH date_range AS (
    -- Get all unique dates from the staging data
    SELECT DISTINCT message_date_only AS full_date
    FROM {{ ref('stg_telegram_messages') }}
    WHERE message_date_only IS NOT NULL
),

date_attributes AS (
    SELECT
        full_date,
        -- Date key as integer (YYYYMMDD format)
        TO_CHAR(full_date, 'YYYYMMDD')::INTEGER AS date_key,
        -- Day attributes
        EXTRACT(DAY FROM full_date) AS day_of_month,
        EXTRACT(ISODOW FROM full_date) AS day_of_week,
        TO_CHAR(full_date, 'Day') AS day_name,
        -- Week attributes
        EXTRACT(WEEK FROM full_date) AS week_of_year,
        -- Month attributes
        EXTRACT(MONTH FROM full_date) AS month,
        TO_CHAR(full_date, 'Month') AS month_name,
        -- Quarter
        EXTRACT(QUARTER FROM full_date) AS quarter,
        -- Year
        EXTRACT(YEAR FROM full_date) AS year,
        -- Weekend flag
        CASE 
            WHEN EXTRACT(ISODOW FROM full_date) IN (6, 7) THEN TRUE 
            ELSE FALSE 
        END AS is_weekend
    FROM date_range
)

SELECT *
FROM date_attributes
ORDER BY full_date
