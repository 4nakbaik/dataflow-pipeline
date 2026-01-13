import os
from sqlalchemy import create_engine, text

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(db_url)

def reset_and_create_tables():
    print("--- Resetting Database for Crypto Pipeline ---")
    
    #Skema untk Data raw
    create_raw_crypto = """
    CREATE TABLE IF NOT EXISTS raw_crypto_prices (
        id SERIAL PRIMARY KEY,
        coin_id VARCHAR(50),
        price_usd DECIMAL(20, 8),
        market_cap DECIMAL(20, 2),
        volume_24h DECIMAL(20, 2),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    #Skema untuk Analytics 
    create_crypto_summary = """
    CREATE TABLE IF NOT EXISTS crypto_summary (
        coin_id VARCHAR(50) PRIMARY KEY,
        avg_price_usd DECIMAL(20, 8),
        max_price_usd DECIMAL(20, 8),
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    drop_old_tables = """
    DROP TABLE IF EXISTS raw_sales;
    DROP TABLE IF EXISTS sales_summary;
    DROP TABLE IF EXISTS raw_crypto_prices; 
    DROP TABLE IF EXISTS crypto_summary;
    """

    try:
        with engine.connect() as conn:
            print("Dropping old tables...")
            conn.execute(text(drop_old_tables))
            
            print("Creating crypto tables...")
            conn.execute(text(create_raw_crypto))
            conn.execute(text(create_crypto_summary))
            conn.commit()
            
        print("--- SUCCESS: Database ready for Crypto Data ---")
        
    except Exception as e:
        print(f"--- ERROR: {e} ---")

if __name__ == "__main__":
    reset_and_create_tables()