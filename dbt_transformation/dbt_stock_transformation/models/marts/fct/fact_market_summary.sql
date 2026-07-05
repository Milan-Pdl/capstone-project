{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='summary_date_key'
) }}

select
    -- Fixed: Remove nullif string logic on dates
    to_char(trade_date, 'YYYYMMDD')::integer as summary_date_key,
    trade_date,
    
    -- Market Aggregations (Safely cast textual numbers if they have empty strings)
    count(distinct stock_symbol) as total_active_stocks,
    sum(case when volume::text = '' then null else volume::bigint end) as total_market_volume,
    sum(case when amount::text = '' then null else amount::numeric end) as total_market_turnover,
    sum(case when no_of_transactions::text = '' then null else no_of_transactions::bigint end) as total_market_transactions,
    
    -- Market Breadth Metrics
    count(case when (case when percent_change::text = '' then null else percent_change::numeric end) > 0 then 1 end) as advancing_stocks,
    count(case when (case when percent_change::text = '' then null else percent_change::numeric end) < 0 then 1 end) as declining_stocks,
    
    current_timestamp as loaded_at
from {{ ref('intermediate_liveShare') }}
where trade_date is not null
group by 1, 2

{% if is_incremental() %}
    -- Filter safely using the date column instead of mixing raw text timestamps
    having trade_date > (select max(trade_date) from {{ this }})
{% endif %}