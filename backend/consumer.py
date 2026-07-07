import os
import json
import logging
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text
from notifier import send_telegram_alert

KAFKA_TOPIC = 'crypto_prices'
KAFKA_BROKER = 'kafka:9092'
DB_URL = os.getenv("DATABASE_URL", "postgresql://kangmus:plprjk1@db:5432/plprjk1_db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_news_link(coin: str) -> str:
    # URL dinamis pencarian berita spesifik per koin
    return f"https://news.google.com/search?q={coin}+crypto+news"

def determine_action(current_price: float, avg_price: float, threshold_pct: float = 2.0) -> str:
    # Algoritma sederhana berbasis deviasi dari harga rata-rata
    if avg_price == 0:
        return "HOLD"
    
    diff_percent = ((current_price - avg_price) / avg_price) * 100
    
    if diff_percent <= -threshold_pct:
        return f"BUY (Turun {abs(diff_percent):.2f}% dari rata-rata)"
    elif diff_percent >= threshold_pct:
        return f"SELL (Naik {diff_percent:.2f}% dari rata-rata)"
    
    return "HOLD"

def run_consumer():
    engine = create_engine(DB_URL)
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='crypto_db_writer_v4',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    fetch_avg = text("SELECT avg_price FROM crypto_summary WHERE coin_id = :coin_id")
    
    insert_raw = text("""
        INSERT INTO raw_crypto_prices (coin_id, price_usd, market_cap, volume_24h)
        VALUES (:coin_id, :price_usd, :market_cap, :volume_24h)
    """)

    upsert_summary = text("""
        INSERT INTO crypto_summary (coin_id, avg_price, max_price, min_price, last_updated)
        VALUES (:coin_id, :price_usd, :price_usd, :price_usd, NOW())
        ON CONFLICT (coin_id) 
        DO UPDATE SET 
            avg_price = (crypto_summary.avg_price + EXCLUDED.avg_price) / 2,
            max_price = GREATEST(crypto_summary.max_price, EXCLUDED.max_price),
            min_price = LEAST(crypto_summary.min_price, EXCLUDED.min_price),
            last_updated = NOW();
    """)

    alert_triggered = {"bitcoin": False}

    for message in consumer:
        data = message.value
        
        try:
            with engine.begin() as conn:
                for coin, stats in data.items():
                    price = stats.get('usd', 0)
                    record = {
                        "coin_id": coin,
                        "price_usd": price,
                        "market_cap": stats.get('usd_market_cap', 0),
                        "volume_24h": stats.get('usd_24h_vol', 0)
                    }

                    # 1. Ambil harga rata-rata sebelum di-update
                    result = conn.execute(fetch_avg, {"coin_id": coin}).fetchone()
                    avg_price = float(result[0]) if result and result[0] else price

                    # 2. Update database
                    conn.execute(insert_raw, record)
                    conn.execute(upsert_summary, record)

                    # 3. Evaluasi kondisi (fokus ke bitcoin sebagai contoh)
                    if coin == 'bitcoin':
                        action = determine_action(price, avg_price)
                        
                        # Trigger pesan hanya jika ada sinyal beli/jual (bukan HOLD)
                        if "BUY" in action or "SELL" in action:
                            if not alert_triggered.get(coin):
                                news = get_news_link(coin)
                                msg = (
                                    f"MARKET SIGNAL: {coin.upper()}\n"
                                    f"Harga Saat Ini: ${price:,.2f}\n"
                                    f"Rekomendasi: {action}\n"
                                    f"Berita Terkait: {news}"
                                )
                                send_telegram_alert(msg)
                                alert_triggered[coin] = True
                        else:
                            # Reset status jika harga kembali stabil (HOLD)
                            alert_triggered[coin] = False
            
            logging.info(f"Processed batch for {len(data)} coins")

        except Exception as e:
            logging.error(f"DB Error: {e}")

if __name__ == "__main__":
    run_consumer()