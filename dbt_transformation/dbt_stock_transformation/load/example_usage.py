"""
Example usage of the live_stock_into_s3 module.

This script demonstrates how to use the LiveShareS3Loader to load data
from the PostgreSQL database into AWS S3 with day-based partitioning.
"""

import os
from live_stock_into_s3 import LiveShareS3Loader


def example_basic_usage():
    """Example 1: Basic usage with default settings."""
    print("Example 1: Basic Usage")
    print("-" * 50)
    
    # Set S3 bucket as environment variable (required)
    os.environ["S3_BUCKET"] = "your-s3-bucket-name"
    os.environ["AWS_ACCESS_KEY_ID"] = "your-aws-access-key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "your-aws-secret-key"
    
    try:
        loader = LiveShareS3Loader()
        loader.run()
        print("✓ Successfully uploaded live_share data to S3\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")


def example_custom_date_column():
    """Example 2: Using a custom date column for partitioning."""
    print("Example 2: Custom Date Column")
    print("-" * 50)
    
    loader = LiveShareS3Loader(
        s3_bucket="your-s3-bucket-name",
        s3_prefix="live_share_data",
        date_column="created_at"  # Use 'created_at' instead of 'date'
    )
    
    try:
        loader.run()
        print("✓ Data uploaded with 'created_at' column for partitioning\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")


def example_custom_database():
    """Example 3: Using custom database connection details."""
    print("Example 3: Custom Database Configuration")
    print("-" * 50)
    
    loader = LiveShareS3Loader(
        db_host="your-db-host",
        db_port=5432,
        db_name="Stock",
        db_user="your-username",
        db_password="your-password",
        s3_bucket="your-s3-bucket-name",
        s3_prefix="live_share_data",
        aws_region="us-west-2"
    )
    
    try:
        loader.run()
        print("✓ Data uploaded from custom database\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")


def example_with_custom_query():
    """Example 4: Using a custom SQL query to filter data."""
    print("Example 4: Custom Query")
    print("-" * 50)
    
    loader = LiveShareS3Loader(s3_bucket="your-s3-bucket-name")
    
    # Query only data from the last 7 days
    custom_query = """
        SELECT * FROM stock.intermediate."live_share"
        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY date DESC
    """
    
    try:
        loader.run(custom_query=custom_query)
        print("✓ Data uploaded using custom query\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")


def environment_variables_setup():
    """
    Guide for setting up environment variables.
    """
    print("Environment Variables Setup")
    print("=" * 50)
    print("""
    Set the following environment variables (or pass them directly):
    
    Database Configuration:
    - DB_HOST: PostgreSQL host (default: localhost)
    - DB_PORT: PostgreSQL port (default: 5432)
    - DB_NAME: Database name (default: Stock)
    - DB_USER: Database user (default: postgres)
    - DB_PASSWORD: Database password (default: milandada)
    
    AWS S3 Configuration:
    - S3_BUCKET: S3 bucket name (REQUIRED)
    - S3_PREFIX: S3 folder path (default: live_share_data)
    - AWS_REGION: AWS region (default: us-east-1)
    - AWS_ACCESS_KEY_ID: AWS access key
    - AWS_SECRET_ACCESS_KEY: AWS secret key
    
    Data Configuration:
    - DATE_COLUMN: Column to partition by (default: date)
    
    Example (PowerShell):
    $env:S3_BUCKET = "my-bucket"
    $env:AWS_ACCESS_KEY_ID = "your-key"
    $env:AWS_SECRET_ACCESS_KEY = "your-secret"
    python live_stock_into_s3.py
    
    Example (Bash):
    export S3_BUCKET="my-bucket"
    export AWS_ACCESS_KEY_ID="your-key"
    export AWS_SECRET_ACCESS_KEY="your-secret"
    python live_stock_into_s3.py
    """)


if __name__ == "__main__":
    # Setup guide
    environment_variables_setup()
    
    # Uncomment the example you want to run:
    # example_basic_usage()
    # example_custom_date_column()
    # example_custom_database()
    # example_with_custom_query()
