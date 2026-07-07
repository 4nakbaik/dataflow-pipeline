import os
import logging
import json
import redis
from datetime import datetime
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text

# --- CONFIG ---
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/pipeline_db")
REDIS_HOST = "redis"
REDIS_PORT = 6379

engine = create_engine(DB_URL)
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
except Exception as e:
    redis_client = None
    print(f"Redis Connection Failed: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Crypto Backend + Redis"}

@app.get("/api/summary")
def get_crypto_summary():
    cache_key = "api:summary"
    
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info("Serving Summary from Cache (Redis)")
            return {"data": json.loads(cached)}

    try:
        query = text("SELECT * FROM crypto_summary")
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = [dict(row._mapping) for row in result]
            
        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps(rows, default=json_serial))
            
        return {"data": rows}
    except Exception as e:
        logger.error(f"Error summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{coin_id}")
def get_coin_history(coin_id: str):
    cache_key = f"api:history:{coin_id}"
    
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Serving History {coin_id} from Cache")
            return {"data": json.loads(cached)}

    try:
        query = text("""
            SELECT coin_id, price_usd, volume_24h, fetched_at as timestamp 
            FROM raw_crypto_prices 
            WHERE coin_id = :coin_id 
            ORDER BY fetched_at ASC 
            LIMIT 500
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"coin_id": coin_id})
            rows = [dict(row._mapping) for row in result]
            
        if not rows:
            return {"data": []}

        if redis_client:
            redis_client.setex(cache_key, 30, json.dumps(rows, default=json_serial))

        return {"data": rows}
    except Exception as e:
        logger.error(f"Error history: {e}")
        return {"data": []}

@app.get("/health")
def health_check():
    redis_status = "connected"
    try:
        redis_client.ping()
    except:
        redis_status = "disconnected"
    return {"db": "ok", "redis": redis_status}