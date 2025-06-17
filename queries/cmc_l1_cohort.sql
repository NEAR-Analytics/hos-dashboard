SELECT DISTINCT
    ch.name
    , ch.symbol
    , ch.market_cap
    , CASE
        WHEN date = today()::date - interval 2 day THEN 'today'
        WHEN date = today()::date - interval 9 day THEN '7d'
        WHEN date = today()::date - interval 16 day THEN '14d'
        WHEN date = today()::date - interval 32 day THEN '30d'
        WHEN date = today()::date - interval 62 day THEN '60d'
        WHEN date = today()::date - interval 92 day THEN '90d'
        WHEN date = today()::date - interval 122 day THEN '120d'
        WHEN date = today()::date - interval 182 day THEN '180d'
    END AS time_period
    , ch.date
FROM external_sources.cmc_coins_history ch
INNER JOIN external_sources.cmc_coins_list_by_category cat
    ON ch.id = cat.id
WHERE TRUE 
    AND date::date in (today()::date - interval 2 day, today()::date - interval 9 day, today()::date - interval 16 day, today()::date - interval 32 day, today()::date - interval 62 day, today()::date - interval 92 day, today()::date - interval 122 day, today()::date - interval 182 day)
    AND cat.category_id = '6433de7df79a2653906cd680'

ORDER BY date DESC, market_cap DESC