-- Fact table for Telegram messages
-- This table contains transactional data with foreign keys to dimension tables

WITH messages AS (
    SELECT
        message_id,
        channel_name,
        message_date,
        message_text,
        message_length,
        views,
        forwards,
        has_image,
        image_path,
        message_date_only
    FROM {{ ref('stg_telegram_messages') }}
),

with_channel_key AS (
    SELECT
        m.*,
        c.channel_key
    FROM messages m
    LEFT JOIN {{ ref('dim_channels') }} c
        ON m.channel_name = c.channel_name
),

with_date_key AS (
    SELECT
        m.*,
        d.date_key
    FROM with_channel_key m
    LEFT JOIN {{ ref('dim_dates') }} d
        ON m.message_date_only = d.full_date
)

SELECT
    -- Foreign keys
    channel_key,
    date_key,
    
    -- Message identifier
    message_id,
    
    -- Message content
    message_text,
    message_length,
    
    -- Engagement metrics
    views,
    forwards,
    
    -- Media information
    has_image,
    image_path,
    
    -- Date for reference
    message_date
FROM with_date_key
WHERE channel_key IS NOT NULL
  AND date_key IS NOT NULL
