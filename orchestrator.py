import time
import logging
import schedule # Kita perlu install library ini dulu nanti
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
    Satu siklus pipeline: Ambil Data -> Olah Data -> Simpan
    """
    logging.info("--- Memulai Siklus Baru ---")
    
    # 1. Trigger Ingestion
    try:
        logging.info("Jalanin Ingestion...")
        run_ingestion(batch_size=5) # Kita kecilin batch biar kelihatan nambahnya pelan-pelan
    except Exception as e:
        logging.error(f"Ingestion Gagal: {e}")
        return # Stop siklus ini jika ingestion gagal

    # 2. Trigger ETL
    try:
        logging.info("Jalanin ETL...")
        run_etl_pipeline()
    except Exception as e:
        logging.error(f"ETL Gagal: {e}")

    logging.info("--- Siklus Selesai. Menunggu siklus berikutnya... ---")

def run_scheduler():
    logging.info("Orchestrator Berjalan. Tekan Ctrl+C untuk berhenti.")
    
    # Jadwalkan job setiap 10 detik (untuk demo)
    # Di dunia nyata, ini mungkin setiap 1 jam atau 1 hari
    schedule.every(10).seconds.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Jalankan sekali saat start agar tidak menunggu 10 detik pertama
    job()
    run_scheduler()