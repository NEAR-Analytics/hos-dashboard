 WITH
labels_private as
(select
    system_created_at,
    address,
    project_name,
    label_type,
    label_subtype,
    creator,
    dim_address_labels_id
from external_sources.flipside_address_labels
union all
select
    _fivetran_synced,
    wallet,
    backer_name,
    'Backer' as label_type,
    fund_name,
    'FIQ' as creator,
    'Null' as dim_address_labels_id
from near_private.backer_wallets 
union all
select
    _fivetran_synced,
    to_account,
    'Core Contributors',
    'Core Contributors',
    'Core Contributors',
    'FIQ' as creator,
    'Null' as dim_address_labels_id
from near_private.core_contributors
union all
select
    _fivetran_synced,
    ft_currency_in,
    'Core Contributors',
    'Core Contributors',
    'Core Contributors',
    'FIQ' as creator,
    'Null' as dim_address_labels_id
from near_private.core_contributors
union all
select
    _fivetran_synced,
    account,
    'NF',
    'NF',
    'NF',
    'FIQ' as creator,
    'Null' as dim_address_labels_id
from near_private.nf_accounts),

top_100 as
(select *
    from external_sources.dune_top_holders where account_id in (select distinct account_id from external_sources.dune_top_holders where epoch_date = '2025-05-20' order by liquid desc, staked desc limit 150)),

diffs as
(select
    epoch_date,    
    account_id,
    project_name,
    label_type,
    liquid,
    unstaked,
    staked,
    lockup_liquid,
    lockup_unstaked,
    lockup_staked
from top_100 h
    left join labels_private l
        on h.account_id = l.address
where epoch_date::date in (today()::date - interval 2 day, today()::date - interval 9 day, today()::date - interval 16 day, today()::date - interval 32 day, today()::date - interval 62 day, today()::date - interval 92 day, today()::date - interval 122 day, today()::date - interval 182 day)
group by all
order by liquid desc)

select *, 
    case
        when epoch_date = today()::date - interval 2 day then 'today'
        when epoch_date = today()::date - interval 9 day then '7d'
        when epoch_date = today()::date - interval 16 day then '14d'
        when epoch_date = today()::date - interval 32 day then '30d'
        when epoch_date = today()::date - interval 62 day then '60d'
        when epoch_date = today()::date - interval 92 day then '90d'
        when epoch_date = today()::date - interval 122 day then '120d'
        when epoch_date = today()::date - interval 182 day then '180d'
    end as time_period
from diffs

