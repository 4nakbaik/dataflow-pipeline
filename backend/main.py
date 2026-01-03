from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="Data Pipeline API", version="1.0.0")

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

class SalesSummary(BaseModel):
    category: str
    total_revenue: float
    transaction_count: int
    class Config:
        from_attributes = True

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/summary", response_model=Dict[str, List[SalesSummary]])
def get_sales_summary():

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT category, total_revenue, transaction_count FROM sales_summary"))
            data = [dict(row._mapping) for row in result]
            
        return {"data": data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")