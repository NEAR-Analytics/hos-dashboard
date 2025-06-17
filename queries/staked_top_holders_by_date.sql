SELECT 
    epoch_date,
    account_id,
    staked
FROM 
    external_sources.dune_top_holders
WHERE TRUE
    AND epoch_date = LEAST('{date_param}'::Date, (SELECT MAX(epoch_date) FROM external_sources.dune_top_holders))
    AND staked > 0