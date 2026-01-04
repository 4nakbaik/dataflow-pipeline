from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import os
import logging

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WowoManiac")

# Koneksi DB
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    DB_URL = "postgresql://user:password@localhost:5432/pipeline_db"

engine = create_engine(DB_URL)

@app.get("/")
def read_root():
    return {"status": "Broker API Active"}

@app.get("/api/summary")
def get_summary():
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM crypto_summary")
            result = conn.execute(query)
            data = [dict(row._mapping) for row in result]
        return {"data": data}
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return {"data": [], "error": str(e)}

@app.get("/api/history/{coin_id}")
def get_coin_history(coin_id: str):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT timestamp, price_usd, volume_24h 
                FROM raw_crypto_prices 
                WHERE coin_id = :coin_id 
                ORDER BY timestamp ASC
                LIMIT 500
            """)
            result = conn.execute(query, {"coin_id": coin_id})
            data = [dict(row._mapping) for row in result]
            
        return {"data": data}
    except Exception as e:
        logger.error(f"History Error: {e}")
        return {"data": [], "error": str(e)}