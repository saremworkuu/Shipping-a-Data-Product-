-- Custom data test: Ensure no messages have future dates
-- This test enforces the business rule that messages should not be dated in the future

SELECT *
FROM {{ ref('stg_telegram_messages') }}
WHERE message_date > CURRENT_TIMESTAMP
