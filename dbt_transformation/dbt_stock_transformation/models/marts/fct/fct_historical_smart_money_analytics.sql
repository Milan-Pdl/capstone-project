with base_history as (

    select * from {{ ref('intermediate_historical_broker_summary') }}

),

-- ---------------------------------------------------------------------
-- 1. Broker Accumulation & Holding Changes
-- ---------------------------------------------------------------------
broker_changes as (

    select
        scraped_date,
        symbol,
        broker_id,
        net_qty,
        lag(net_qty) over (partition by symbol, broker_id order by scraped_date) as prev_net_qty,
        (net_qty - lag(net_qty) over (partition by symbol, broker_id order by scraped_date)) as abs_holding_change,
        round(
            100.0 * (net_qty - lag(net_qty) over (partition by symbol, broker_id order by scraped_date)) / 
            nullif(abs(lag(net_qty) over (partition by symbol, broker_id order by scraped_date)), 0), 2
        ) as pct_holding_change
    from base_history

),

-- ---------------------------------------------------------------------
-- 2. Stock Sentiment & Breadth Analysis
-- ---------------------------------------------------------------------
stock_sentiment as (

    select
        scraped_date,
        symbol,
        sum(case when net_qty > 0 then net_qty else 0 end) as net_qty_accumulated,
        sum(case when net_qty < 0 then abs(net_qty) else 0 end) as net_qty_distributed,
        count(distinct case when net_qty > 0 then broker_id end) as num_accumulating_brokers,
        count(distinct case when net_qty < 0 then broker_id end) as num_distributing_brokers,
        count(distinct broker_id) as total_active_brokers
    from base_history
    group by 1, 2

),

-- ---------------------------------------------------------------------
-- 3. Concentration Analysis (CR3 Index) & Herding Score
-- ---------------------------------------------------------------------
concentration_prep as (

    select
        scraped_date,
        symbol,
        broker_id,
        net_qty,
        sum(abs(net_qty)) over (partition by scraped_date, symbol) as total_symbol_volume,
        row_number() over (partition by scraped_date, symbol order by abs(net_qty) desc) as vol_rank
    from base_history

),

concentration_metrics as (

    select
        scraped_date,
        symbol,
        -- Combined concentration percentage controlled by top 3 brokers
        round(100.0 * sum(case when vol_rank <= 3 then abs(net_qty) else 0 end) / nullif(max(total_symbol_volume), 0), 2) as cr3_concentration_pct
    from concentration_prep
    group by 1, 2

),

-- ---------------------------------------------------------------------
-- 4. Conviction Score & Herding Engine
-- ---------------------------------------------------------------------
combined_metrics as (

    select
        s.scraped_date,
        s.symbol,
        s.net_qty_accumulated,
        s.net_qty_distributed,
        s.num_accumulating_brokers,
        s.num_distributing_brokers,
        s.total_active_brokers,
        c.cr3_concentration_pct,

        -- Sentiment Label
        case 
            when s.net_qty_accumulated > (s.net_qty_distributed * 1.5) then 'BULLISH'
            when s.net_qty_distributed > (s.net_qty_accumulated * 1.5) then 'BEARISH'
            else 'NEUTRAL'
        end as sentiment_label,

        -- Herding Score (0-100 scale: high value indicates extreme unbalance/herding)
        round(
            100.0 * abs(s.num_accumulating_brokers - s.num_distributing_brokers) / nullif(s.total_active_brokers, 0), 2
        ) as herding_score,

        -- Broker Conviction Score (0-100 scale: combines CR3 concentration and buy breadth)
        least(100, round(
            (c.cr3_concentration_pct * 0.6) + 
            ((s.net_qty_accumulated / nullif(s.net_qty_accumulated + s.net_qty_distributed, 0)) * 40), 2
        )) as conviction_score

    from stock_sentiment s
    join concentration_metrics c 
        on s.scraped_date = c.scraped_date 
       and s.symbol = c.symbol

)

-- ---------------------------------------------------------------------
-- 5. Final Assembly: Flags, Alerts & Early Breakouts
-- ---------------------------------------------------------------------
select
    m.scraped_date,
    m.symbol,
    m.net_qty_accumulated,
    m.net_qty_distributed,
    m.num_accumulating_brokers,
    m.num_distributing_brokers,
    m.sentiment_label,
    m.cr3_concentration_pct,
    m.herding_score,
    m.conviction_score,

    -- High Concentration Flag
    case when m.cr3_concentration_pct >= 65.0 then true else false end as is_high_concentration,

    -- Early Breakout Detection Flag
    case 
        when m.sentiment_label = 'BULLISH' 
         and m.cr3_concentration_pct >= 55.0 
         and m.num_accumulating_brokers <= 5 
         and m.conviction_score >= 70
        then true else false 
    end as flag_potential_early_breakout,

    -- Unusual Activity Alerts
    case 
        when m.herding_score >= 80.0 then 'ALERT: EXTREME_HERDING_DETECTED'
        when m.cr3_concentration_pct >= 75.0 then 'ALERT: UNUSUAL_CORNERING_BY_TOP_BROKERS'
        when m.sentiment_label = 'BULLISH' and m.conviction_score >= 85 then 'ALERT: INSTITUTIONAL_ACCUMULATION_SURGE'
        else 'NORMAL'
    end as unusual_activity_alert

from combined_metrics m