-- Custom data test: Ensure view counts are non-negative
-- This test enforces the business rule that view counts should never be negative

SELECT *
FROM {{ ref('stg_telegram_messages') }}
WHERE views < 0
