import os
import requests
import sys

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_telegram_chat_id():
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN belom diset di file .env nih.")
        return

    print(f"--- Memeriksa Token: {TOKEN[:5]}... (hidden) ---")
    
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get("ok"):
            print(f"Error dari Telegram API: {data}")
            return

        result = data.get("result", [])

        if not result:
            print("\n[!] Hasil Kosong.")
            print("TIPS: Coba Kirim pesan apapun ke bot,terus jalanin script ini lagi.")
            return
        
        latest_message = result[-1]
        chat_id = latest_message["message"]["chat"]["id"]
        username = latest_message["message"]["chat"].get("username", "Unknown")

        print("\n" + "="*40)
        print("GUDD! CHAT ID KETEMU")
        print("="*40)
        print(f"Username : @{username}")
        print(f"Chat ID  : {chat_id}")
        print("="*40)
        print(f"\nSung salin '{chat_id}' ke variabel TELEGRAM_CHAT_ID di file .env.")

    except Exception as e:
        print(f"Terjadi kesalahan koneksi: {e}")

if __name__ == "__main__":
    get_telegram_chat_id()