import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, text

# Kredensial DB disesuaikan dengan arsitektur Podman Anda
DB_URL = "postgresql://kangmus:plprjk1@db:5432/plprjk1_db"

DEFAULT_ARGS = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

def clean_old_data():
    """Fungsi untuk menghapus data mentah yang lebih tua dari 7 hari."""
    engine = create_engine(DB_URL)
    
    # Query untuk menghapus data berdasarkan kolom waktu (fetched_at)
    delete_query = text("""
        DELETE FROM raw_crypto_prices
        WHERE fetched_at < NOW() - INTERVAL '7 days';
    """)
    
    try:
        with engine.begin() as conn:
            result = conn.execute(delete_query)
            # rowcount akan menampilkan jumlah baris yang berhasil dihapus
            logging.info(f"Maintenance Sukses: Menghapus {result.rowcount} baris data lama.")
    except Exception as e:
        logging.error(f"Gagal melakukan maintenance database: {e}")
        raise e

with DAG(
    dag_id='db_retention_cleanup',
    default_args=DEFAULT_ARGS,
    description='Job harian untuk membersihkan data raw_crypto_prices berumur > 7 hari',
    schedule_interval='0 0 * * *', # Cron expression untuk jam 00:00 setiap hari
    catchup=False,
    tags=['maintenance', 'database', 'cleanup'],
) as dag:

    cleanup_task = PythonOperator(
        task_id='delete_old_records',
        python_callable=clean_old_data
    )

    cleanup_task