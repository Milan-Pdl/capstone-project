from __future__ import annotations

import psycopg2
import requests

from config import COMPANY_TABLE, DB_CONFIG, RAW_SCHEMA, STOCK_TABLE

COMPANIES_URL = "https://nepalipaisa.com/api/GetCompanies"
SHARE_PRICE_URL = "https://nepalipaisa.com/api/GetTodaySharePrice"

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://nepalipaisa.com/",
    "X-Requested-With": "XMLHttpRequest",
}

def get_qualified_table(table_name: str) -> str:
    return f"{RAW_SCHEMA}.{table_name}"


def fetch_companies() -> list[dict]:
    response = requests.post(
        COMPANIES_URL,
        json=[],
        headers=API_HEADERS,
        timeout=60,
    )

    response.raise_for_status()

    companies = response.json()["result"]

    print(f"Fetched {len(companies)} companies")

    return companies


def load_companies(companies: list[dict]) -> None:

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    company_table = get_qualified_table(COMPANY_TABLE)

    cursor.execute(f"""
        CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA};
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {company_table} (
            company_id INT,
            company_name VARCHAR,
            stock_symbol VARCHAR,
            sector_id INT,
            sector_name VARCHAR
        );
    """)

    cursor.execute(f"TRUNCATE TABLE {company_table};")

    insert_query = f"""
        INSERT INTO {company_table}
        (
            company_id,
            company_name,
            stock_symbol,
            sector_id,
            sector_name
        )
        VALUES (%s,%s,%s,%s,%s);
    """

    rows = [
        (
            c["companyId"],
            c["companyName"],
            c["stockSymbol"],
            c["sectorId"],
            c["sectorName"],
        )
        for c in companies
    ]

    cursor.executemany(insert_query, rows)

    conn.commit()

    cursor.close()
    conn.close()

    print(f"Inserted {len(rows)} companies")


def fetch_share_prices() -> list[dict]:

    response = requests.get(
        SHARE_PRICE_URL,
        params={"stockSymbol": ""},
        headers=API_HEADERS,
        timeout=60,
    )

    response.raise_for_status()

    stocks = response.json()["result"]["stocks"]

    print(f"Fetched {len(stocks)} stocks")

    return stocks

def load_share_prices(stocks: list[dict]) -> None:

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    stock_table = get_qualified_table(STOCK_TABLE)

    cursor.execute(f"""
        CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA};
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {stock_table} (

            stock_symbol VARCHAR,
            company_name VARCHAR,
            no_of_transactions INT,
            max_price NUMERIC,
            min_price NUMERIC,
            opening_price NUMERIC,
            closing_price NUMERIC,
            amount NUMERIC,
            previous_closing NUMERIC,
            difference_rs NUMERIC,
            percent_change NUMERIC,
            volume INT,
            ltv INT,
            as_of_date TIMESTAMP,
            as_of_date_string VARCHAR,
            trade_date DATE,
            data_type VARCHAR

        );
    """)

    cursor.execute(f"TRUNCATE TABLE {stock_table};")

    insert_query = f"""
        INSERT INTO {stock_table}
        (
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
            trade_date,
            data_type
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """

    rows = [
        (
            s["stockSymbol"],
            s["companyName"],
            s["noOfTransactions"],
            s["maxPrice"],
            s["minPrice"],
            s["openingPrice"],
            s["closingPrice"],
            s["amount"],
            s["previousClosing"],
            s["differenceRs"],
            s["percentChange"],
            s["volume"],
            s["ltv"],
            s["asOfDate"],
            s["asOfDateString"],
            s["tradeDate"],
            s["dataType"],
        )
        for s in stocks
    ]

    cursor.executemany(insert_query, rows)

    conn.commit()

    cursor.close()
    conn.close()

    print(f"Inserted {len(rows)} stock records")

if __name__ == "__main__":

    companies = fetch_companies()
    load_companies(companies)

    stocks = fetch_share_prices()
    load_share_prices(stocks)

    print("Data loaded successfully.")