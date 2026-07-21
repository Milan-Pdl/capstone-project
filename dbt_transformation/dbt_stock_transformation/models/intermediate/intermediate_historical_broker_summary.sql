with staged as (

    select * from {{ ref('stg_broker_holding') }}

),

-- Keep latest run per day across history
latest_scrape_per_day as (

    select
        *,
        row_number() over (
            partition by scraped_date, symbol, broker_id, transaction_type 
            order by scraped_at desc
        ) as rn
    from staged

),

deduped as (

    select * from latest_scrape_per_day where rn = 1

)

select
    scraped_date,
    symbol,
    broker_id,
    sum(case when lower(transaction_type) = 'buy' then quantity else 0 end) as buy_qty,
    sum(case when lower(transaction_type) = 'sell' then quantity else 0 end) as sell_qty,
    sum(case when lower(transaction_type) = 'buy' then quantity else -quantity end) as net_qty
from deduped
group by 1, 2, 3