import os
import requests
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

COINS = "bitcoin,ethereum,solana,ripple,cardano"
URL = f"https://api.coingecko.com/api/v3/simple/price?ids={COINS}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true"

def fetch_crypto_prices():
    logging.info("Calling API...")
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        return None

def run_ingestion():
    logging.info("Starting ingestion...")
    
    data = fetch_crypto_prices()
    if not data:
        return

    query = text("""
        INSERT INTO raw_crypto_prices (coin_id, price_usd, market_cap, volume_24h)
        VALUES (:coin_id, :price_usd, :market_cap, :volume_24h)
    """)

    try:
        # engine.begin() handles transaction commit automatically
        with engine.begin() as conn:
            for coin, stats in data.items():
                record = {
                    "coin_id": coin,
                    "price_usd": stats.get('usd', 0),
                    "market_cap": stats.get('usd_market_cap', 0),
                    "volume_24h": stats.get('usd_24h_vol', 0)
                }
                conn.execute(query, record)
            
        logging.info(f"Successfully ingested prices for {len(data)} coins.")
            
    except Exception as e:
        logging.error(f"Database insertion failed: {e}")

if __name__ == "__main__":
    run_ingestion()