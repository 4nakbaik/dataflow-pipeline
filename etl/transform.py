import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

def extract_data(db_engine: Engine) -> pd.DataFrame:
    """Fetches raw data from the database."""
    query = "SELECT product_category, amount, transaction_id FROM raw_sales"
    return pd.read_sql(query, db_engine)

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates sales data by category."""
    if df.empty:
        return pd.DataFrame()

    # Aggregation logic: Sum amount and count transactions
    summary = df.groupby('product_category').agg(
        total_revenue=('amount', 'sum'),
        transaction_count=('transaction_id', 'count')
    ).reset_index()
    
    summary.rename(columns={'product_category': 'category'}, inplace=True)
    return summary

def load_data(df: pd.DataFrame, db_engine: Engine, table_name: str = 'sales_summary') -> None:
    """Loads transformed data into the analytics table."""
    if df.empty:
        logging.warning("No data to load.")
        return

    try:
        # Using 'replace' for simplicity; consider 'upsert' for production
        df.to_sql(table_name, db_engine, if_exists='replace', index=False)
        
        # Re-apply primary key constraint after replacement
        with db_engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (category);"))
            conn.commit()
            
        logging.info(f"Successfully loaded {len(df)} rows into {table_name}.")
        
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        raise

def run_etl_pipeline():
    """Orchestrates the ETL process."""
    logging.info("Starting ETL pipeline...")
    
    raw_df = extract_data(engine)
    logging.info(f"Extracted {len(raw_df)} records.")
    
    clean_df = transform_data(raw_df)
    
    load_data(clean_df, engine)
    logging.info("ETL pipeline completed successfully.")

if __name__ == "__main__":
    run_etl_pipeline()