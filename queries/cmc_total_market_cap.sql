SELECT
    date,
    'Total Crypto Market' as name,
    'TOTAL MC' as symbol,
    sum(market_cap) as market_cap,
    CASE
        WHEN date = today()::date - interval 2 day THEN 'today'
        WHEN date = today()::date - interval 9 day THEN '7d'
        WHEN date = today()::date - interval 16 day THEN '14d'
        WHEN date = today()::date - interval 32 day THEN '30d'
        WHEN date = today()::date - interval 62 day THEN '60d'
        WHEN date = today()::date - interval 92 day THEN '90d'
        WHEN date = today()::date - interval 122 day THEN '120d'
        WHEN date = today()::date - interval 182 day THEN '180d'
    END AS time_period
FROM external_sources.cmc_coins_history
WHERE date::date in (today()::date - interval 2 day, today()::date - interval 9 day, today()::date - interval 16 day, today()::date - interval 32 day, today()::date - interval 62 day, today()::date - interval 92 day, today()::date - interval 122 day, today()::date - interval 182 day)
GROUP BY ALL