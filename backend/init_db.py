import os
from sqlalchemy import create_engine, text

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(db_url)

def create_tables():
    print("--- Starting Manual Table Creation ---")
    
    create_raw_sales = """
    CREATE TABLE IF NOT EXISTS raw_sales (
        id SERIAL PRIMARY KEY,
        transaction_id VARCHAR(50),
        product_category VARCHAR(50),
        amount DECIMAL(10, 2),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_sales_summary = """
    CREATE TABLE IF NOT EXISTS sales_summary (
        category VARCHAR(50) PRIMARY KEY,
        total_revenue DECIMAL(15, 2),
        transaction_count INT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(create_raw_sales))
            print("Created table: raw_sales")
            
            conn.execute(text(create_sales_summary))
            print("Created table: sales_summary")
            
            conn.commit()
            
        print("--- SUCCESS: All tables created manually ---")
        
    except Exception as e:
        print(f"--- ERROR: {e} ---")

if __name__ == "__main__":
    create_tables()