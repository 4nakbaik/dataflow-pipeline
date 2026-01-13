import time
import logging
import schedule
from ingestion.fetch_data import run_ingestion
from etl.transform import run_etl_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ORCHESTRATOR] - %(message)s',
    datefmt='%H:%M:%S'
)

def job():
    logging.info("--- Starting Pipeline Cycle ---")
    
    #Trigger Ingestion
    try:
        logging.info("Running Ingestion...")
        run_ingestion() 
    except Exception as e:
        logging.error(f"Ingestion Failed: {e}")
        return

    #Trigger ETL
    try:
        logging.info("Running ETL...")
        run_etl_pipeline()
    except Exception as e:
        logging.error(f"ETL Failed: {e}")

    logging.info("--- Cycle Completed. Waiting for next schedule... ---")

def run_scheduler():
    logging.info("Orchestrator Started. Press Ctrl+C to stop.")
    schedule.every(60).seconds.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    job()
    run_scheduler()