import os
import time
import random
import uuid
import logging
from typing import Dict, Any
from sqlalchemy import create_engine, text

# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database config
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

engine = create_engine(DB_URL)
CATEGORIES = ['Electronics', 'Clothing', 'Groceries', 'Books']

def generate_transaction() -> Dict[str, Any]:
    return {
        "transaction_id": str(uuid.uuid4()),
        "product_category": random.choice(CATEGORIES),
        "amount": round(random.uniform(10.0, 500.0), 2)
    }

def run_ingestion(batch_size: int = 10) -> None:
    logging.info("Starting data ingestion process.")
    
    query = text("""
        INSERT INTO raw_sales (transaction_id, product_category, amount)
        VALUES (:transaction_id, :product_category, :amount)
    """)

    try:
        with engine.connect() as conn:
            for _ in range(batch_size):
                data = generate_transaction()
                conn.execute(query, data)
            conn.commit()
            
        logging.info(f"Successfully ingested {batch_size} records into raw_sales.")
        
    except Exception as e:
        logging.error(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    time.sleep(2)
    run_ingestion()