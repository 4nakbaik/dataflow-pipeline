import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

def extract_data(db_engine: Engine) -> pd.DataFrame:
    query = "SELECT coin_id, price_usd, timestamp FROM raw_crypto_prices"
    try:
        return pd.read_sql(query, db_engine)
    except Exception as e:
        logging.error(f"Error extracting data (Table might be missing): {e}")
        return pd.DataFrame()

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    summary = df.groupby('coin_id').agg(
        avg_price_usd=('price_usd', 'mean'),
        max_price_usd=('price_usd', 'max'),
        last_updated=('timestamp', 'max')
    ).reset_index()

    return summary

def load_data(df: pd.DataFrame, db_engine: Engine, table_name: str = 'crypto_summary') -> None:
    if df.empty:
        logging.warning("No data to load.")
        return

    try:
        df.to_sql(table_name, db_engine, if_exists='replace', index=False)

        with db_engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (coin_id);"))
            conn.commit()
            
        logging.info(f"Successfully loaded {len(df)} rows into {table_name}.")
        
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        raise

def run_etl_pipeline():
    logging.info("Starting ETL pipeline...")
    
    raw_df = extract_data(engine)
    logging.info(f"Extracted {len(raw_df)} records.")
    
    clean_df = transform_data(raw_df)
    
    load_data(clean_df, engine)
    logging.info("ETL pipeline completed successfully.")

if __name__ == "__main__":
    run_etl_pipeline()