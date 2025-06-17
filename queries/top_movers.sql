SELECT 
    *
FROM external_sources.flipside_top_movers
WHERE utc_date >= today()::date - interval 90 day
ORDER BY utc_date desc, amount desc