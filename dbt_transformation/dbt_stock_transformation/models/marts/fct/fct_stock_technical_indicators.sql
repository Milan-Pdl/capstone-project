{{ config(
    materialized='table'
) }}

with daily_base as (
    select 
        fsp.stock_date_key,
        fsp.company_key,
        fds.trade_date,
        fds.closing_price,
        fds.volume,
        fsp.percent_change as daily_return,
        fsp.price_difference_rs
    from {{ ref('fact_stock_performance') }} fsp
    join {{ ref('fact_daily_stock') }} fds on fsp.stock_date_key = fds.stock_date_key
),

moving_averages as (
    select
        *,
        -- 1. 5/20/50-Day Moving Averages
        avg(closing_price) over(
            partition by company_key 
            order by trade_date 
            rows between 4 preceding and current row
        )::numeric(18,2) as ma_5_day,
        
        avg(closing_price) over(
            partition by company_key 
            order by trade_date 
            rows between 19 preceding and current row
        )::numeric(18,2) as ma_20_day,
        
        avg(closing_price) over(
            partition by company_key 
            order by trade_date 
            rows between 49 preceding and current row
        )::numeric(18,2) as ma_50_day,

        -- 2. Rolling Volume (20-day Average Volume)
        avg(volume) over(
            partition by company_key 
            order by trade_date 
            rows between 19 preceding and current row
        )::bigint as rolling_volume_20_day,

        -- 3. Volatility (20-day standard deviation of daily returns)
        stddev(daily_return) over(
            partition by company_key 
            order by trade_date 
            rows between 19 preceding and current row
        )::numeric(18,4) as rolling_volatility_20_day
    from daily_base
)

select
    stock_date_key,
    company_key,
    trade_date,
    closing_price,
    volume,
    
    -- Chart 1: Moving Averages
    ma_5_day,
    ma_20_day,
    ma_50_day,
    
    -- Chart 2: Rolling Volume
    rolling_volume_20_day,
    
    -- Chart 3: Volatility
    rolling_volatility_20_day,
    
    -- Chart 4: Daily Return
    daily_return,
    
    -- Chart 5: Price Momentum (Rate of Change - 14 Day Price Delta %)
    ((closing_price - lag(closing_price, 14) over(partition by company_key order by trade_date)) 
        / nullif(lag(closing_price, 14) over(partition by company_key order by trade_date), 0) * 100)::numeric(18,2) as momentum_roc_14_day
from moving_averages