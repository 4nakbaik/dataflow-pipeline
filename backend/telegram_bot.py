import os
import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL", "postgresql://kangmus:plprjk1@db:5432/plprjk1_db")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")

bot = telebot.TeleBot(TOKEN)
engine = create_engine(DB_URL)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = "Bot monitoring crypto aktif. Gunakan perintah /info untuk melihat data harga terbaru. - 4nakbaik"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['info'])
def send_coin_options(message):
    # Setup interactive buttons for 15 assets
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Bitcoin", callback_data="bitcoin"),
        InlineKeyboardButton("Ethereum", callback_data="ethereum"),
        InlineKeyboardButton("Solana", callback_data="solana"),
        InlineKeyboardButton("Cardano", callback_data="cardano"),
        InlineKeyboardButton("Binance Coin", callback_data="binancecoin"),
        InlineKeyboardButton("Dogecoin", callback_data="dogecoin"),
        InlineKeyboardButton("Shiba Inu", callback_data="shiba-inu"),
        InlineKeyboardButton("Polkadot", callback_data="polkadot"),
        InlineKeyboardButton("Avalanche", callback_data="avalanche-2"),
        InlineKeyboardButton("Chainlink", callback_data="chainlink"),
        InlineKeyboardButton("Polygon", callback_data="polygon"),
        InlineKeyboardButton("Uniswap", callback_data="uniswap"),
        InlineKeyboardButton("Litecoin", callback_data="litecoin"),
        InlineKeyboardButton("Stellar", callback_data="stellar"),
        InlineKeyboardButton("Ripple", callback_data="ripple")
    )
    
    bot.send_message(
        message.chat.id, 
        "Pilih aset untuk melihat informasi harga terkini:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    coin_id = call.data
    
    query = text("""
        SELECT avg_price, max_price, min_price, last_updated 
        FROM crypto_summary 
        WHERE coin_id = :coin_id
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"coin_id": coin_id}).fetchone()
            
        if result:
            avg_price, max_price, min_price, last_updated = result
            msg = (
                f"DATA ASET: {coin_id.upper()}\n"
                f"Harga Rata-rata: ${avg_price:,.2f}\n"
                f"Harga Tertinggi: ${max_price:,.2f}\n"
                f"Harga Terendah: ${min_price:,.2f}\n"
                f"Pembaruan Terakhir: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            msg = f"Data untuk {coin_id.upper()} belum tersedia di database."
            
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, msg)
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        bot.answer_callback_query(call.id, "Terjadi kesalahan sistem.")

if __name__ == "__main__":
    logging.info("Telegram Bot listener started...")
    bot.infinity_polling()