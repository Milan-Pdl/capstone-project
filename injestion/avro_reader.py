from fastavro import reader
import pandas as pd

records = []

with open(r"E:\DLytiica\capstone_project\injestion\0ae708c3-a664-4c58-abd5-36553c4190e2-m0.avro", "rb") as f:
    for record in reader(f):
        records.append(record)

df = pd.DataFrame(records)

print(df.head())