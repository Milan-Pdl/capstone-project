import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

df = pd.read_csv(
    r"E:\DLytiica\capstone_project\injestion\broker_holding_2026-07-21.csv",
    on_bad_lines="skip"  # skip malformed rows
)

conn = psycopg2.connect(
    host="localhost",
    database="Stock",
    user="postgres",
    password="milandada",
    port=5432
)

records = list(df.itertuples(index=False, name=None))

query = """
INSERT INTO raw.broker_holding
(
    broker,
    quantity,
    type,
    symbol,
    period_range,
    scraped_at
)
VALUES %s
"""

with conn.cursor() as cur:
    execute_values(cur, query, records)

conn.commit()
conn.close()

print(f"Inserted {len(records)} rows successfully.")