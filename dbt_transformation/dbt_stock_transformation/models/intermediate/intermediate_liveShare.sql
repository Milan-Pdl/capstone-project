
{{ config(
    materialized='incremental',
    incremental_strategy = 'append',
    unique_key='stock_date_key'
) }}



select
    stock_date_key,
    stock_symbol::text as stock_symbol,
    company_name::text as company_name,
    nullif(no_of_transactions, '')::bigint as no_of_transactions,
    nullif(max_price, '')::numeric as max_price,
    nullif(min_price, '')::numeric as min_price,
    nullif(opening_price, '')::numeric as opening_price,
    nullif(closing_price, '')::numeric as closing_price,
    nullif(amount, '')::numeric as amount,
    nullif(previous_closing, '')::numeric as previous_closing,
    nullif(difference_rs, '')::numeric as difference_rs,
    nullif(percent_change, '')::numeric as percent_change,
    nullif(volume, '')::bigint as volume,
    nullif(ltv, '')::numeric as ltv,
    nullif(as_of_date, '')::timestamp as as_of_date,
    as_of_date_string::text as as_of_date_string,
    nullif(trade_date, '')::date as trade_date,
    current_timestamp as loaded_at
from {{ ref('stg_liveShare') }}

{% if is_incremental() %}
    -- Keeps the lookback efficient
    where as_of_date::timestamp > (select max(as_of_date) from {{ this }})
{% endif %}