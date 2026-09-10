#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام برای قیمت‌ها - نسخه Termux
بدون مشکل httpx/httpcore - استفاده مستقیم از Telegram API
"""

import requests
import json
import time
import logging
from datetime import datetime

# تنظیمات logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== تنظیمات ==========
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # جایگزین کنید
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
UPDATE_OFFSET = 0

# ========== تابع‌های قیمت‌ها ==========

def get_gold_silver_prices():
    """دریافت قیمت طلا و نقره"""
    try:
        response = requests.get(
            'https://api.metals.live/v1/spot/metals',
            timeout=10
        )
        data = response.json()
        
        gold_price = data.get('gold', 0) / 31.1035
        silver_price = data.get('silver', 0) / 31.1035
        
        return {
            'gold': round(gold_price, 2),
            'silver': round(silver_price, 2)
        }
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت‌ها: {e}")
        return None

def get_currency_rates():
    """دریافت نرخ ارزها"""
    try:
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=10
        )
        data = response.json()
        
        rates = data.get('rates', {})
        
        return {
            'usd_to_eur': round(rates.get('EUR', 0.85), 4),
            'eur_to_usd': round(1 / rates.get('EUR', 0.85), 4)
        }
    except Exception as e:
        logger.error(f"خطا در دریافت ارز: {e}")
        return None

# ========== API تلگرام ==========

def send_message(chat_id, text, reply_markup=None):
    """ارسال پیام"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {e}")
        return False

def get_updates(offset=0):
    """دریافت پیام‌های جدید"""
    url = f"{TELEGRAM_API_URL}/getUpdates"
    
    try:
        response = requests.get(
            url,
            params={'offset': offset, 'timeout': 30},
            timeout=35
        )
        return response.json()
    except Exception as e:
        logger.error(f"خطا در دریافت update‌ها: {e}")
        return {'ok': False}

# ========== صفحه‌بندی ==========

def get_keyboard():
    """ایجاد صفحه‌کلید"""
    return {
        'keyboard': [
            [{'text': '💰 قیمت لحظه‌ای'}],
            [{'text': '🥇 طلا و نقره'}, {'text': '💵 ارزها'}],
            [{'text': 'ℹ️ درباره'}]
        ],
        'resize_keyboard': True
    }

# ========== پیام‌های ربات ==========

def handle_message(message):
    """پردازش پیام‌های دریافتی"""
    chat_id = message['chat']['id']
    text = message.get('text', '').strip()
    
    logger.info(f"پیام از {chat_id}: {text}")
    
    if text == '/start' or text == '/help':
        send_start(chat_id)
    
    elif text == '💰 قیمت لحظه‌ای':
        send_all_prices(chat_id)
    
    elif text == '🥇 طلا و نقره':
        send_metals(chat_id)
    
    elif text == '💵 ارزها':
        send_currencies(chat_id)
    
    elif text == 'ℹ️ درباره':
        send_about(chat_id)
    
    else:
        send_message(chat_id, "لطفاً از دکمه‌های موجود استفاده کنید.", get_keyboard())

def send_start(chat_id):
    """دستور شروع"""
    text = """🤖 به ربات قیمت‌ها خوش آمدید!

من قیمت‌های لحظه‌ای را نشان می‌دهم:

• 🥇 طلا و نقره
• 💵 دلار و یورو

از دکمه‌های زیر استفاده کنید:"""
    
    send_message(chat_id, text, get_keyboard())

def send_all_prices(chat_id):
    """نمایش تمام قیمت‌ها"""
    metals = get_gold_silver_prices()
    currencies = get_currency_rates()
    
    if not metals or not currencies:
        send_message(chat_id, "❌ متأسفانه نتوانستم قیمت‌ها را دریافت کنم.")
        return
    
    text = f"""📊 *قیمت‌های لحظه‌ای*

🥇 *طلا:* ${metals['gold']}/گرم
🥈 *نقره:* ${metals['silver']}/گرم

💵 *دلار:* 1 USD = {currencies['usd_to_eur']} EUR
💶 *یورو:* 1 EUR = {currencies['eur_to_usd']} USD

🕐 *آپدیت:* {datetime.now().strftime('%H:%M:%S')}"""
    
    send_message(chat_id, text, get_keyboard())

def send_metals(chat_id):
    """نمایش طلا و نقره"""
    metals = get_gold_silver_prices()
    
    if not metals:
        send_message(chat_id, "❌ نتوانستم قیمت‌های طلا و نقره را دریافت کنم.")
        return
    
    text = f"""🥇 *قیمت طلا*
💰 ${metals['gold']}/گرم
💰 ${metals['gold'] * 31.1035:.2f}/اونس

🥈 *قیمت نقره*
💰 ${metals['silver']}/گرم
💰 ${metals['silver'] * 31.1035:.2f}/اونس

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    send_message(chat_id, text, get_keyboard())

def send_currencies(chat_id):
    """نمایش ارزها"""
    currencies = get_currency_rates()
    
    if not currencies:
        send_message(chat_id, "❌ نتوانستم نرخ ارزها را دریافت کنم.")
        return
    
    text = f"""💵 *دلار (USD)*
🔄 1 دلار = {currencies['usd_to_eur']} یورو

💶 *یورو (EUR)*
🔄 1 یورو = {currencies['eur_to_usd']} دلار

🕐 *آپدیت:* {datetime.now().strftime('%H:%M:%S')}"""
    
    send_message(chat_id, text, get_keyboard())

def send_about(chat_id):
    """درباره ربات"""
    text = """ℹ️ *درباره این ربات*

🤖 *ربات قیمت‌ها*
نسخه: 2.0 (Termux)

✨ ویژگی‌ها:
• قیمت لحظه‌ای طلا و نقره
• نرخ ارزهای رایج
• بدون مشکل Termux!

📊 منابع داده:
• Metals Live API
• Exchange Rate API

🔗 توجه:
قیمت‌ها برای اطلاع است.
برای معاملات واقعی منابع رسمی را بررسی کنید."""
    
    send_message(chat_id, text, get_keyboard())

# ========== حلقه اصلی ==========

def main():
    """برنامه اصلی"""
    global UPDATE_OFFSET
    
    print("✅ ربات در حال اجرا است...")
    print("برای متوقف کردن Ctrl+C را فشار دهید\n")
    
    try:
        while True:
            try:
                result = get_updates(UPDATE_OFFSET)
                
                if result.get('ok') and result.get('result'):
                    for update in result['result']:
                        update_id = update['update_id']
                        UPDATE_OFFSET = update_id + 1
                        
                        if 'message' in update:
                            message = update['message']
                            handle_message(message)
                
                time.sleep(0.5)
            
            except Exception as e:
                logger.error(f"خطا در حلقه اصلی: {e}")
                time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n\n👋 ربات متوقف شد.")

if __name__ == '__main__':
    # بررسی توکن
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ لطفاً BOT_TOKEN را جایگزین کنید!")
        exit(1)
    
    main()
