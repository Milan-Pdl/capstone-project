{{ config(
    incremental_strategy='delete+insert',
    unique_key='stock_date_key'
) }}

select
    -- Keys
    stock_date_key,
    md5(stock_symbol) as company_key, 
    
    -- Fixed: Restored the missing to_char function name and casted to integer
    to_char(trade_date, 'YYYYMMDD')::integer as date_key,
    
    -- Performance Metrics
    case when difference_rs::text = '' then null else difference_rs::numeric end as price_difference_rs,
    case when percent_change::text = '' then null else percent_change::numeric end as percent_change,
    case when ltv::text = '' then null else ltv::numeric end as ltv,
    
    -- Analytical Flags
    case 
        when (case when percent_change::text = '' then null else percent_change::numeric end) > 0 then 'Gain'
        when (case when percent_change::text = '' then null else percent_change::numeric end) < 0 then 'Loss'
        else 'Flat'
    end as daily_direction,
    
    -- Audit Metadata
    current_timestamp as loaded_at
from {{ ref('intermediate_liveShare') }}
where trade_date is not null

{% if is_incremental() %}
    -- Filter safely using the actual date data type instead of breaking string logic
    and trade_date > (select max(trade_date) from {{ this }})
{% endif %}