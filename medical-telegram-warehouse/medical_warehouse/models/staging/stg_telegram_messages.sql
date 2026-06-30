-- Staging model for Telegram messages
-- This model cleans and standardizes raw Telegram data

WITH source AS (
    SELECT *
    FROM {{ source('raw', 'telegram_messages') }}
),

renamed AS (
    SELECT
        -- Primary key
        message_id,
        
        -- Channel information
        channel_name,
        
        -- Date information
        CAST(message_date AS TIMESTAMP) AS message_date,
        
        -- Message content
        TRIM(message_text) AS message_text,
        
        -- Media information
        has_media,
        image_path,
        
        -- Engagement metrics
        COALESCE(views, 0) AS views,
        COALESCE(forwards, 0) AS forwards,
        
        -- Metadata
        loaded_at
        
    FROM source
),

cleaned AS (
    SELECT
        *,
        -- Calculate message length
        LENGTH(message_text) AS message_length,
        -- Create has_image flag
        CASE 
            WHEN image_path IS NOT NULL THEN TRUE 
            ELSE FALSE 
        END AS has_image,
        -- Extract date part for joining
        CAST(message_date AS DATE) AS message_date_only
        
    FROM renamed
    WHERE message_text IS NOT NULL 
        AND LENGTH(TRIM(message_text)) > 0
        AND message_date IS NOT NULL
)

SELECT *
FROM cleaned
