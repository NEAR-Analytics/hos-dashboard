SELECT 
    * 
    , liquid + unstaked + staked + reward + lockup_liquid + lockup_unstaked + lockup_staked + lockup_reward AS total
    , CASE
        WHEN epoch_date = today()::date - interval 2 day THEN 'today'
        WHEN epoch_date = today()::date - interval 9 day THEN '7d'
        WHEN epoch_date = today()::date - interval 16 day THEN '14d'
        WHEN epoch_date = today()::date - interval 32 day THEN '30d'
        WHEN epoch_date = today()::date - interval 62 day THEN '60d'
        WHEN epoch_date = today()::date - interval 92 day THEN '90d'
        WHEN epoch_date = today()::date - interval 122 day THEN '120d'
        WHEN epoch_date = today()::date - interval 182 day THEN '180d'
    END AS time_period
from external_sources.dune_top_holders
WHERE TRUE 
    AND epoch_date IN (
        today()::date - interval 2 day
        , today()::date - interval 9 day 
        , today()::date - interval 16 day
        , today()::date - interval 32 day
        , today()::date - interval 62 day
        , today()::date - interval 92 day
        , today()::date - interval 122 day
        , today()::date - interval 182 day
    )
