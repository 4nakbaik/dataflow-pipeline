import json
import time
import requests
import logging
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

KAFKA_BROKER = 'kafka:9092'
TOPIC_NAME = 'crypto_prices'

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Mengganti dan menambah daftar koin menjadi 15 aset populer
COINS = (
    "bitcoin,ethereum,solana,ripple,cardano,"
    "binancecoin,dogecoin,shiba-inu,polkadot,avalanche-2,"
    "chainlink,polygon,uniswap,litecoin,stellar"
)
URL = f"https://api.coingecko.com/api/v3/simple/price?ids={COINS}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true"

def fetch_and_produce():
    try:
        logging.info("Fetching data from CoinGecko...")
        response = requests.get(URL, timeout=10)
        data = response.json()
        
        producer.send(TOPIC_NAME, value=data)
        producer.flush()
        
        logging.info(f"Sent {len(data)} coins to Kafka topic '{TOPIC_NAME}'")
    except Exception as e:
        logging.error(f"Failed to produce: {e}")

if __name__ == "__main__":
    while True:
        fetch_and_produce()
        time.sleep(30)