{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='stock_date_key'
) }}

select
    stock_date_key,
    md5(stock_symbol) as company_key,
    stock_symbol,
    company_name,
    -- No trimming or casting needed if it's already a date!
    to_char(trade_date, 'YYYYMMDD')::integer as date_key,
    trade_date,
    
    -- Handle as_of_date safely (cast to timestamp if it is still text)
    case 
        when as_of_date::text = '' then null 
        else as_of_date::timestamp 
    end as as_of_date,
    
    -- Core metrics (assuming these are still text strings with possible empty values)
    case when closing_price::text = '' then null else closing_price::numeric end as closing_price,
    case when opening_price::text = '' then null else opening_price::numeric end as opening_price,
    case when max_price::text = '' then null else max_price::numeric end as max_price,
    case when min_price::text = '' then null else min_price::numeric end as min_price,
    case when previous_closing::text = '' then null else previous_closing::numeric end as previous_closing,
    case when volume::text = '' then null else volume::bigint end as volume,
    case when amount::text = '' then null else amount::numeric end as amount,
    case when no_of_transactions::text = '' then null else no_of_transactions::bigint end as no_of_transactions,
    
    current_timestamp as loaded_at
from {{ ref('intermediate_liveShare') }}
where trade_date is not null

{% if is_incremental() %}
    -- Dynamically filter for new data using the trade_date
    and trade_date > (select max(trade_date) from {{ this }})
{% endif %}