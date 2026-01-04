import time
import logging
import schedule
from ingestion.fetch_data import run_ingestion
from etl.transform import run_etl_pipeline

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ORCHESTRATOR] - %(message)s',
    datefmt='%H:%M:%S'
)

def job():
    """
    Executes one full pipeline cycle: Ingestion -> ETL.
    """
    logging.info("--- Starting Pipeline Cycle ---")
    
    # 1. Trigger Ingestion
    try:
        logging.info("Running Ingestion...")
        # FIX: Removed argument 'batch_size' as API ingestion doesn't need it
        run_ingestion() 
    except Exception as e:
        logging.error(f"Ingestion Failed: {e}")
        return

    # 2. Trigger ETL
    try:
        logging.info("Running ETL...")
        run_etl_pipeline()
    except Exception as e:
        logging.error(f"ETL Failed: {e}")

    logging.info("--- Cycle Completed. Waiting for next schedule... ---")

def run_scheduler():
    logging.info("Orchestrator Started. Press Ctrl+C to stop.")
    
    # Set to 60 seconds to respect CoinGecko API Rate Limits (approx 10-30 req/min free tier)
    schedule.every(60).seconds.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Run once immediately on startup
    job()
    run_scheduler()