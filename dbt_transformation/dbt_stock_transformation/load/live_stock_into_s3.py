"""
Script to load data from stock.intermediate.live_share table into AWS S3
with day-based partitioning using Parquet format.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import sql
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiveShareS3Loader:
    """Load live_share data from PostgreSQL to AWS S3 with day-based partitioning."""
    
    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_name: str = "Stock",
        db_user: str = "postgres",
        db_password: str = "milandada",
        aws_access_key: str = None,
        aws_secret_key: str = None,
        aws_region: str = "us-east-1",
        s3_bucket: str = None,
        s3_prefix: str = "live_share_data",
        date_column: str = "date"  # Column to use for partitioning
    ):
        """
        Initialize the loader with database and AWS S3 credentials.
        
        Args:
            db_host: PostgreSQL host
            db_port: PostgreSQL port
            db_name: PostgreSQL database name
            db_user: PostgreSQL user
            db_password: PostgreSQL password
            aws_access_key: AWS access key (uses env var if None)
            aws_secret_key: AWS secret key (uses env var if None)
            aws_region: AWS region
            s3_bucket: S3 bucket name
            s3_prefix: S3 prefix/folder path
            date_column: Column name to partition by
        """
        self.db_config = {
            "host": db_host,
            "port": db_port,
            "dbname": db_name,
            "user": db_user,
            "password": db_password,
        }
        
        self.s3_bucket = s3_bucket or os.getenv("S3_BUCKET")
        self.s3_prefix = s3_prefix
        self.date_column = date_column
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            region_name=aws_region,
            aws_access_key_id=aws_access_key or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        
        if not self.s3_bucket:
            raise ValueError("S3_BUCKET must be provided or set as environment variable")
    
    def connect_to_db(self):
        """Establish connection to PostgreSQL database."""
        try:
            conn = psycopg2.connect(**self.db_config)
            logger.info("Successfully connected to PostgreSQL database")
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def fetch_data(self, conn, query: str = None) -> pd.DataFrame:
        """
        Fetch data from the database.
        
        Args:
            conn: PostgreSQL connection object
            query: Custom SQL query (if None, fetches all from stock.intermediate.live_share)
        
        Returns:
            DataFrame with the fetched data
        """
        if query is None:
            query = 'SELECT * FROM stock.intermediate."live_share"'
        
        try:
            logger.info(f"Executing query: {query}")
            df = pd.read_sql_query(query, conn)
            logger.info(f"Fetched {len(df)} rows from database")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            raise
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for S3 upload.
        
        Args:
            df: Input DataFrame
        
        Returns:
            Processed DataFrame with proper data types
        """
        # Convert date column to datetime if it exists
        if self.date_column in df.columns:
            df[self.date_column] = pd.to_datetime(df[self.date_column])
        
        logger.info("Data prepared for upload")
        return df
    
    def upload_to_s3_partitioned(self, df: pd.DataFrame) -> None:
        """
        Upload data to S3 with day-based partitioning.
        
        Partitions data by year/month/day format: s3://bucket/prefix/year=YYYY/month=MM/day=DD/
        
        Args:
            df: DataFrame to upload
        """
        if df.empty:
            logger.warning("DataFrame is empty, skipping upload")
            return
        
        # Group data by date
        grouped = df.groupby(df[self.date_column].dt.date)
        
        total_files = len(grouped)
        logger.info(f"Uploading data partitioned into {total_files} files")
        
        for date_val, group_df in grouped:
            try:
                # Create partition path: year=YYYY/month=MM/day=DD
                partition_path = (
                    f"{self.s3_prefix}/"
                    f"year={date_val.year}/"
                    f"month={date_val.month:02d}/"
                    f"day={date_val.day:02d}/"
                    f"data.parquet"
                )
                
                # Convert to Parquet in memory
                parquet_buffer = group_df.to_parquet(index=False)
                
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=partition_path,
                    Body=parquet_buffer,
                    ContentType="application/octet-stream"
                )
                
                logger.info(
                    f"Uploaded {len(group_df)} rows for {date_val} "
                    f"to s3://{self.s3_bucket}/{partition_path}"
                )
                
            except ClientError as e:
                logger.error(f"Failed to upload partition for {date_val}: {e}")
                raise
        
        logger.info(f"Successfully uploaded all {total_files} partitions to S3")
    
    def run(self, custom_query: str = None) -> None:
        """
        Execute the full pipeline: fetch data from DB and upload to S3.
        
        Args:
            custom_query: Optional custom SQL query
        """
        conn = None
        try:
            logger.info("Starting live_share data pipeline")
            
            # Connect to database
            conn = self.connect_to_db()
            
            # Fetch data
            df = self.fetch_data(conn, custom_query)
            
            if df.empty:
                logger.warning("No data fetched from database")
                return
            
            # Prepare data
            df = self.prepare_data(df)
            
            # Upload to S3
            self.upload_to_s3_partitioned(df)
            
            logger.info("Pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.info("Database connection closed")


def main():
    """Main entry point for the script."""
    
    # Initialize loader with credentials from environment or defaults
    loader = LiveShareS3Loader(
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "Stock"),
        db_user=os.getenv("DB_USER", "postgres"),
        db_password=os.getenv("DB_PASSWORD", "milandada"),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        s3_bucket=os.getenv("S3_BUCKET"),
        s3_prefix=os.getenv("S3_PREFIX", "live_share_data"),
        date_column=os.getenv("DATE_COLUMN", "date")
    )
    
    # Run the pipeline
    loader.run()


if __name__ == "__main__":
    main()
