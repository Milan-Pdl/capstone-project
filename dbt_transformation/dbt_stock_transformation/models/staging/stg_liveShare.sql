{{ config(
    materialized='incremental',
    incremental_strategy = 'append',
    unique_key='stock_date_key'
) }}

select
    -- Generating the surrogate key
    {{ dbt_utils.generate_surrogate_key(['stock_symbol', 'as_of_date']) }} as stock_date_key,
    
    stock_symbol,
    company_name,
    no_of_transactions,
    max_price,
    min_price,
    opening_price,
    closing_price,
    amount,
    previous_closing,
    difference_rs,
    percent_change,
    volume,
    ltv,
    as_of_date,
    as_of_date_string,
    trade_date
from {{ source('stock', 'stock_market_data') }}

{% if is_incremental() %}
    -- Keeps the lookback efficient
    where as_of_date > (select max(as_of_date) from {{ this }})
{% endif %}