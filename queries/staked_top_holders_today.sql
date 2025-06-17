
SELECT 
    epoch_date,
    account_id,
    staked
FROM 
    external_sources.dune_top_holders
WHERE 
    epoch_date = (SELECT MAX(epoch_date) FROM external_sources.dune_top_holders)