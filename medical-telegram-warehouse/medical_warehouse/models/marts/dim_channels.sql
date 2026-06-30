-- Dimension table for Telegram channels
-- This table contains channel-level attributes and metrics

WITH channel_stats AS (
    SELECT
        channel_name,
        COUNT(*) AS total_posts,
        SUM(views) AS total_views,
        AVG(views) AS avg_views,
        SUM(forwards) AS total_forwards,
        MIN(message_date) AS first_post_date,
        MAX(message_date) AS last_post_date,
        SUM(CASE WHEN has_image THEN 1 ELSE 0 END) AS total_image_posts
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name
),

channel_classification AS (
    SELECT
        *,
        -- Classify channel type based on name
        CASE 
            WHEN channel_name ILIKE '%chem%' OR channel_name ILIKE '%medic%' THEN 'Medical'
            WHEN channel_name ILIKE '%cosmetic%' OR channel_name ILIKE '%lobelia%' THEN 'Cosmetics'
            WHEN channel_name ILIKE '%pharma%' OR channel_name ILIKE '%tikvah%' THEN 'Pharmaceutical'
            ELSE 'Other'
        END AS channel_type
    FROM channel_stats
),

with_surrogate_key AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY channel_name) AS channel_key,
        *
    FROM channel_classification
)

SELECT
    channel_key,
    channel_name,
    channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    total_views,
    avg_views,
    total_forwards,
    total_image_posts,
    ROUND((total_image_posts::NUMERIC / NULLIF(total_posts, 0)) * 100, 2) AS image_post_percentage
FROM with_surrogate_key
