WITH month_starts AS (
  -- Define snapshot dates: 1st of each month from Jan to June 2025
  SELECT DATE '2025-01-01' AS snapshot_date UNION ALL
  SELECT DATE '2025-02-01' UNION ALL
  SELECT DATE '2025-03-01' UNION ALL
  SELECT DATE '2025-04-01' UNION ALL
  SELECT DATE '2025-05-01' UNION ALL
  SELECT DATE '2025-06-01'
),

whale_snapshots AS (
  -- Get whales on each snapshot date
  SELECT
    ms.snapshot_date,
    dth.account_id,
    dth.liquid,
    dth.unstaked,
    dth.staked,
    dth.reward,
    dth.lockup_liquid,
    dth.lockup_unstaked,
    dth.lockup_staked,
    dth.lockup_reward,
    dth.liquid + dth.unstaked + dth.staked + dth.reward + dth.lockup_liquid + dth.lockup_unstaked + dth.lockup_staked + dth.lockup_reward AS total
  FROM month_starts ms
  JOIN external_sources.dune_top_holders dth
    ON dth.epoch_date = ms.snapshot_date
  --WHERE dth.liquid > 100000
)

-- Final output: snapshot date and whale accounts
SELECT
  snapshot_date,
  account_id,
  liquid,
  unstaked,
  staked,
  reward,
  lockup_liquid,
  lockup_unstaked,
  lockup_staked,
  lockup_reward,
  total,
  labels.*
FROM whale_snapshots ws
LEFT JOIN external_sources.flipside_address_labels AS labels
  ON ws.account_id = labels.address
