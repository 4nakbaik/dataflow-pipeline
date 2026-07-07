import json
import time
import requests
import logging
from kafka import KafkaProducer

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Konfigurasi Kafka
KAFKA_BROKER = 'kafka:9092'
TOPIC_NAME = 'crypto_prices'

# Inisialisasi Producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8') # Auto convert JSON ke Bytes
)

COINS = "bitcoin,ethereum,solana,ripple,cardano"
URL = f"https://api.coingecko.com/api/v3/simple/price?ids={COINS}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true"

def fetch_and_produce():
    try:
        logging.info("Fetching data from CoinGecko...")
        response = requests.get(URL, timeout=10)
        data = response.json()
        
        # Kirim data ke Kafka
        # Kita kirim sebagai satu paket JSON utuh
        producer.send(TOPIC_NAME, value=data)
        producer.flush() # Pastikan data terkirim
        
        logging.info(f"Sent data to Kafka topic '{TOPIC_NAME}'")
        
    except Exception as e:
        logging.error(f"Failed to produce: {e}")

if __name__ == "__main__":
    # Loop sederhana untuk simulasi streaming (tiap 30 detik)
    while True:
        fetch_and_produce()
        time.sleep(30)