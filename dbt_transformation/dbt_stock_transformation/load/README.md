# Live Share to S3 Data Loader

This script loads data from your PostgreSQL `stock.intermediate."live_share"` table into AWS S3 with day-based partitioning in Parquet format.

## Features

- ✅ Connects to PostgreSQL database
- ✅ Fetches data from `stock.intermediate."live_share"` table
- ✅ Partitions data by date (year/month/day structure)
- ✅ Uploads to AWS S3 in Parquet format
- ✅ Comprehensive error handling and logging
- ✅ Flexible configuration options

## Installation

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

Or install individual packages:

```bash
pip install psycopg2 pandas boto3 pyarrow python-dotenv
```

## Configuration

### Option 1: Environment Variables (Recommended)

Set environment variables before running the script:

**PowerShell:**
```powershell
$env:S3_BUCKET = "my-bucket"
$env:AWS_ACCESS_KEY_ID = "your-access-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
$env:AWS_REGION = "us-east-1"
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "Stock"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "milandada"
$env:S3_PREFIX = "live_share_data"
$env:DATE_COLUMN = "date"
```

**Bash/Linux/macOS:**
```bash
export S3_BUCKET="my-bucket"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="Stock"
export DB_USER="postgres"
export DB_PASSWORD="milandada"
export S3_PREFIX="live_share_data"
export DATE_COLUMN="date"
```

### Option 2: .env File

Create a `.env` file in the script directory:

```
S3_BUCKET=my-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Stock
DB_USER=postgres
DB_PASSWORD=milandada
S3_PREFIX=live_share_data
DATE_COLUMN=date
```

Then load it:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 3: Direct Arguments

Pass configuration directly in Python:

```python
from live_stock_into_s3 import LiveShareS3Loader

loader = LiveShareS3Loader(
    db_host="localhost",
    db_port=5432,
    db_name="Stock",
    db_user="postgres",
    db_password="milandada",
    aws_access_key="your-access-key",
    aws_secret_key="your-secret-key",
    aws_region="us-east-1",
    s3_bucket="my-bucket",
    s3_prefix="live_share_data",
    date_column="date"
)
loader.run()
```

## Usage

### Basic Usage

```bash
python -m live_stock_into_s3
```

Or as a module:

```python
from live_stock_into_s3 import LiveShareS3Loader

loader = LiveShareS3Loader(s3_bucket="my-bucket")
loader.run()
```

### With Custom Query

```python
from live_stock_into_s3 import LiveShareS3Loader

loader = LiveShareS3Loader(s3_bucket="my-bucket")

# Query only recent data
query = """
    SELECT * FROM stock.intermediate."live_share"
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
"""

loader.run(custom_query=query)
```

### With Custom Date Column

```python
loader = LiveShareS3Loader(
    s3_bucket="my-bucket",
    date_column="created_at"  # Use created_at instead of date
)
loader.run()
```

## S3 Partition Structure

Data is partitioned with the following S3 key structure:

```
s3://your-bucket/live_share_data/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/data.parquet
│   │   ├── day=02/data.parquet
│   │   └── ...
│   ├── month=02/
│   │   └── ...
│   └── ...
├── year=2025/
│   └── ...
```

This partition structure is ideal for:
- **Hive-style partitioning** (compatible with Athena, Spark, etc.)
- **Efficient querying** of specific date ranges
- **Data organization** and maintenance

## Logging

The script logs all operations to console. Example output:

```
2024-01-15 10:30:45,123 - INFO - Starting live_share data pipeline
2024-01-15 10:30:45,456 - INFO - Successfully connected to PostgreSQL database
2024-01-15 10:30:45,789 - INFO - Executing query: SELECT * FROM stock.intermediate."live_share"
2024-01-15 10:30:46,012 - INFO - Fetched 50000 rows from database
2024-01-15 10:30:46,234 - INFO - Data prepared for upload
2024-01-15 10:30:46,456 - INFO - Uploading data partitioned into 5 files
2024-01-15 10:30:48,789 - INFO - Uploaded 10000 rows for 2024-01-11 to s3://my-bucket/live_share_data/year=2024/month=01/day=11/data.parquet
...
2024-01-15 10:30:50,123 - INFO - Successfully uploaded all 5 partitions to S3
```

## AWS S3 Permissions

Ensure your AWS credentials have the following S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket",
        "arn:aws:s3:::your-bucket/*"
      ]
    }
  ]
}
```

## Examples

See `example_usage.py` for various usage examples:

```bash
python example_usage.py
```

## Troubleshooting

### PostgreSQL Connection Error
- Verify database host, port, user, and password
- Ensure PostgreSQL is running
- Check firewall/network connectivity

### AWS Authentication Error
- Verify AWS credentials are correct
- Check AWS credentials have S3 permissions
- Ensure IAM user is active

### S3 Bucket Error
- Verify bucket exists in the specified region
- Check bucket name is correct
- Ensure IAM permissions include the bucket

### Memory Error (for large datasets)
- Consider using custom query to filter data
- Process data in smaller date ranges
- Increase available system memory

## Performance Notes

- For large datasets (>1GB), processing time depends on network and storage performance
- Parquet format provides ~5-10x compression vs CSV
- Partitioning enables efficient parallel processing in data warehouses

## License

This script is part of the Capstone Project.
