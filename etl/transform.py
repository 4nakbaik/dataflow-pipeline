import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.append(os.getcwd())
try:
    from backend.notifier import send_telegram_alert
except ImportError:
    def send_telegram_alert(msg): logging.warning("Telegram notifier not found.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

def extract_data(db_engine: Engine) -> pd.DataFrame:
    query = "SELECT coin_id, price_usd, fetched_at FROM raw_crypto_prices"
    try:
        df = pd.read_sql(query, db_engine)
        df.rename(columns={'fetched_at': 'timestamp'}, inplace=True)
        return df
    except Exception as e:
        logging.error(f"Error extracting data: {e}")
        return pd.DataFrame()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def process_alerts(df: pd.DataFrame):
    if df.empty: return

    unique_coins = df['coin_id'].unique()

    for coin in unique_coins:
        coin_df = df[df['coin_id'] == coin].sort_values('timestamp')
        
        if len(coin_df) < 15: continue

        coin_df['RSI'] = calculate_rsi(coin_df['price_usd'])
        
        last_row = coin_df.iloc[-1]
        rsi = last_row['RSI']
        price = last_row['price_usd']
        
        msg = ""
        if rsi < 30:
            msg = f"BUY SIGNAL: {coin.upper()}\nPrice: ${price:,.2f}\nRSI: {rsi:.2f} (Oversold)"
        elif rsi > 70:
            msg = f"SELL SIGNAL: {coin.upper()}\nPrice: ${price:,.2f}\nRSI: {rsi:.2f} (Overbought)"
            
        if msg:
            logging.info(f"Triggering alert for {coin}")
            try:
                send_telegram_alert(msg)
            except Exception as e:
                logging.error(f"Failed to send alert: {e}")

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()

    summary = df.groupby('coin_id').agg(
        avg_price=('price_usd', 'mean'),
        max_price=('price_usd', 'max'),
        min_price=('price_usd', 'min'),
        last_updated=('timestamp', 'max')
    ).reset_index()

    return summary

def load_data(df: pd.DataFrame, db_engine: Engine, table_name: str = 'crypto_summary') -> None:
    if df.empty:
        logging.warning("No data to load.")
        return

    try:
        with db_engine.begin() as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (coin_id);"))
            
        logging.info(f"Successfully loaded {len(df)} rows into {table_name}.")
        
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        raise

def run_etl_pipeline():
    logging.info("Starting ETL pipeline...")
    
    raw_df = extract_data(engine)
    logging.info(f"Extracted {len(raw_df)} records.")
    
    if raw_df.empty:
        logging.error("Raw data is empty. Ensure ingestion ran successfully.")
        return

    try:
        process_alerts(raw_df)
    except Exception as e:
        logging.error(f"Alert processing failed: {e}")

    clean_df = transform_data(raw_df)
    load_data(clean_df, engine)
    
    logging.info("ETL pipeline completed successfully.")

if __name__ == "__main__":
    run_etl_pipeline()