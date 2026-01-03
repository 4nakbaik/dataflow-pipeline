import time
import logging
import schedule 
from ingestion.fetch_data import run_ingestion
from etl.transform import run_etl_pipeline

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ORCHESTRATOR] - %(message)s',
    datefmt='%H:%M:%S'
)

def job():
    logging.info("--- Memulai Siklus Baru ---")
    
    try:
        logging.info("Jalanin Ingestion...")
        run_ingestion(batch_size=5) # Kita kecilin batch biar kelihatan nambahnya pelan-pelan
    except Exception as e:
        logging.error(f"Ingestion Gagal: {e}")
        return 

    try:
        logging.info("Jalanin ETL...")
        run_etl_pipeline()
    except Exception as e:
        logging.error(f"ETL Gagal: {e}")

    logging.info("--- Siklus Selesai. Menunggu siklus berikutnya... ---")

def run_scheduler():
    logging.info("Orchestrator Berjalan. Tekan Ctrl+C untuk berhenti.")
    schedule.every(10).seconds.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    job()
    run_scheduler()