#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام برای قیمت‌ها - API تجو (TGJU)
✅ قیمت‌های ریالی (طلا، نقره، دلار، یورو)
✅ بدون مشکل SSL
✅ Termux Compatible
"""

import requests
import json
import time
import logging
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# غیرفعال کردن هشدار SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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

# تنظیمات requests برای Termux
REQUESTS_TIMEOUT = 15
VERIFY_SSL = False

# ========== API تجو (TGJU) ==========

def get_tgju_prices():
    """
    دریافت قیمت‌های طلا، نقره، دلار و یورو از تجو
    منبع: https://tgju.org/api/v1/latest
    """
    try:
        url = "https://tgju.org/api/v1/latest"
        
        response = requests.get(
            url,
            timeout=REQUESTS_TIMEOUT,
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        data = response.json()
        
        prices = {}
        
        # استخراج قیمت‌ها از پاسخ
        if 'gold_and_coin' in data:
            if 'gold' in data['gold_and_coin']:
                gold = data['gold_and_coin']['gold']
                prices['gold'] = {
                    'price': gold.get('price', 0),
                    'change': gold.get('change', 0)
                }
            
            if 'silver' in data['gold_and_coin']:
                silver = data['gold_and_coin']['silver']
                prices['silver'] = {
                    'price': silver.get('price', 0),
                    'change': silver.get('change', 0)
                }
        
        # دلار
        if 'currency' in data:
            if 'usd' in data['currency']:
                usd = data['currency']['usd']
                prices['usd'] = {
                    'price': usd.get('price', 0),
                    'change': usd.get('change', 0)
                }
            
            # یورو
            if 'eur' in data['currency']:
                eur = data['currency']['eur']
                prices['eur'] = {
                    'price': eur.get('price', 0),
                    'change': eur.get('change', 0)
                }
        
        prices['updated'] = datetime.now().strftime('%H:%M:%S')
        prices['source'] = 'TGJU.ORG'
        
        return prices
    
    except requests.exceptions.SSLError as e:
        logger.error(f"❌ SSL Error: {str(e)[:50]}...")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ خطا در دریافت قیمت‌ها: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطا در تحلیل JSON: {e}")
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
        response = requests.post(
            url,
            json=payload,
            timeout=REQUESTS_TIMEOUT,
            verify=VERIFY_SSL
        )
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
            params={'offset': offset, 'timeout': 25},
            timeout=35,
            verify=VERIFY_SSL
        )
        return response.json()
    except Exception as e:
        logger.error(f"خطا در دریافت update‌ها: {e}")
        return {'ok': False}

# ========== صفحه‌کلید ==========

def get_keyboard():
    """ایجاد صفحه‌کلید"""
    return {
        'keyboard': [
            [{'text': '💰 قیمت لحظه‌ای'}],
            [{'text': '🥇 طلا'}, {'text': '🥈 نقره'}],
            [{'text': '💵 دلار'}, {'text': '💶 یورو'}],
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
    
    elif text == '🥇 طلا':
        send_gold(chat_id)
    
    elif text == '🥈 نقره':
        send_silver(chat_id)
    
    elif text == '💵 دلار':
        send_usd(chat_id)
    
    elif text == '💶 یورو':
        send_eur(chat_id)
    
    elif text == 'ℹ️ درباره':
        send_about(chat_id)
    
    else:
        send_message(chat_id, "لطفاً از دکمه‌های موجود استفاده کنید.", get_keyboard())

def format_price(price, currency_symbol='تومان'):
    """قالب‌بندی قیمت با فاصل"""
    if isinstance(price, (int, float)):
        return f"{int(price):,} {currency_symbol}"
    return "N/A"

def get_change_emoji(change):
    """دریافت emoji برای تغییر قیمت"""
    if change > 0:
        return f"📈 +{change}%"
    elif change < 0:
        return f"📉 {change}%"
    else:
        return "➡️ ۰%"

def send_start(chat_id):
    """دستور شروع"""
    text = """🤖 به ربات قیمت‌های لحظه‌ای خوش آمدید!

🇮🇷 *قیمت‌های ریالی از تجو:*

• 🥇 طلا
• 🥈 نقره
• 💵 دلار
• 💶 یورو

از دکمه‌های زیر استفاده کنید:"""
    
    send_message(chat_id, text, get_keyboard())

def send_all_prices(chat_id):
    """نمایش تمام قیمت‌ها"""
    prices = get_tgju_prices()
    
    if not prices:
        send_message(chat_id, "❌ متأسفانه نتوانستم قیمت‌ها را دریافت کنم.\n\nلطفاً دوباره تلاش کنید.", get_keyboard())
        return
    
    text = "📊 *قیمت‌های لحظه‌ای*\n\n"
    
    # طلا
    if 'gold' in prices:
        gold = prices['gold']
        text += f"🥇 *طلا:*\n"
        text += f"   💰 {format_price(gold['price'])}\n"
        text += f"   {get_change_emoji(gold['change'])}\n\n"
    
    # نقره
    if 'silver' in prices:
        silver = prices['silver']
        text += f"🥈 *نقره:*\n"
        text += f"   💰 {format_price(silver['price'])}\n"
        text += f"   {get_change_emoji(silver['change'])}\n\n"
    
    # دلار
    if 'usd' in prices:
        usd = prices['usd']
        text += f"💵 *دلار (USD):*\n"
        text += f"   💰 {format_price(usd['price'])}\n"
        text += f"   {get_change_emoji(usd['change'])}\n\n"
    
    # یورو
    if 'eur' in prices:
        eur = prices['eur']
        text += f"💶 *یورو (EUR):*\n"
        text += f"   💰 {format_price(eur['price'])}\n"
        text += f"   {get_change_emoji(eur['change'])}\n\n"
    
    text += f"🕐 *آپدیت:* {prices['updated']}\n"
    text += f"📡 *منبع:* {prices['source']}"
    
    send_message(chat_id, text, get_keyboard())

def send_gold(chat_id):
    """نمایش قیمت طلا"""
    prices = get_tgju_prices()
    
    if not prices or 'gold' not in prices:
        send_message(chat_id, "❌ نتوانستم قیمت طلا را دریافت کنم.", get_keyboard())
        return
    
    gold = prices['gold']
    text = f"""🥇 *قیمت طلا*

💰 *قیمت:* {format_price(gold['price'])}
📊 *تغییر:* {get_change_emoji(gold['change'])}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📡 منبع: {prices['source']}"""
    
    send_message(chat_id, text, get_keyboard())

def send_silver(chat_id):
    """نمایش قیمت نقره"""
    prices = get_tgju_prices()
    
    if not prices or 'silver' not in prices:
        send_message(chat_id, "❌ نتوانستم قیمت نقره را دریافت کنم.", get_keyboard())
        return
    
    silver = prices['silver']
    text = f"""🥈 *قیمت نقره*

💰 *قیمت:* {format_price(silver['price'])}
📊 *تغییر:* {get_change_emoji(silver['change'])}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📡 منبع: {prices['source']}"""
    
    send_message(chat_id, text, get_keyboard())

def send_usd(chat_id):
    """نمایش قیمت دلار"""
    prices = get_tgju_prices()
    
    if not prices or 'usd' not in prices:
        send_message(chat_id, "❌ نتوانستم قیمت دلار را دریافت کنم.", get_keyboard())
        return
    
    usd = prices['usd']
    text = f"""💵 *قیمت دلار (USD)*

💰 *قیمت:* {format_price(usd['price'])}
📊 *تغییر:* {get_change_emoji(usd['change'])}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📡 منبع: {prices['source']}"""
    
    send_message(chat_id, text, get_keyboard())

def send_eur(chat_id):
    """نمایش قیمت یورو"""
    prices = get_tgju_prices()
    
    if not prices or 'eur' not in prices:
        send_message(chat_id, "❌ نتوانستم قیمت یورو را دریافت کنم.", get_keyboard())
        return
    
    eur = prices['eur']
    text = f"""💶 *قیمت یورو (EUR)*

💰 *قیمت:* {format_price(eur['price'])}
📊 *تغییر:* {get_change_emoji(eur['change'])}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📡 منبع: {prices['source']}"""
    
    send_message(chat_id, text, get_keyboard())

def send_about(chat_id):
    """درباره ربات"""
    text = """ℹ️ *درباره این ربات*

🤖 *ربات قیمت‌های لحظه‌ای*
نسخه: 4.0 (TGJU)

✨ ویژگی‌ها:
• ✅ قیمت لحظه‌ای طلا و نقره
• ✅ قیمت دلار و یورو (ریالی)
• ✅ بدون مشکل SSL
• ✅ کار در Termux
• ✅ تغییرات قیمت

📊 منابع داده:
• TGJU.ORG API

🇮🇷 *تمام قیمت‌ها بر اساس ریال ایران است*

💡 نکته:
برای معاملات واقعی منابع رسمی را بررسی کنید."""
    
    send_message(chat_id, text, get_keyboard())

# ========== حلقه اصلی ==========

def main():
    """برنامه اصلی"""
    global UPDATE_OFFSET
    
    print("=" * 60)
    print("✅ ربات قیمت‌های لحظه‌ای (TGJU) در حال اجرا است...")
    print("🇮🇷 منبع: TGJU.ORG")
    print("🔒 SSL/TLS: ثابت‌شده")
    print("=" * 60)
    print("برای متوقف کردن Ctrl+C را فشار دهید\n")
    
    error_count = 0
    max_errors = 20
    
    # تست اولیه اتصال
    print("🔍 تست اتصال به TGJU.ORG...")
    test_prices = get_tgju_prices()
    if test_prices:
        print("✅ اتصال موفق!\n")
    else:
        print("⚠️ هشدار: نتوانستم اتصال برقرار کنم. ربات ادامه می‌دهد...\n")
    
    try:
        while True:
            try:
                result = get_updates(UPDATE_OFFSET)
                
                if result.get('ok') and result.get('result'):
                    error_count = 0  # ریست کردن شمارنده خطا
                    for update in result['result']:
                        update_id = update['update_id']
                        UPDATE_OFFSET = update_id + 1
                        
                        if 'message' in update:
                            message = update['message']
                            handle_message(message)
                
                time.sleep(0.5)
            
            except requests.exceptions.ConnectionError as e:
                error_count += 1
                logger.warning(f"⚠️ خطای اتصال ({error_count}/{max_errors})")
                time.sleep(5)
            
            except Exception as e:
                error_count += 1
                logger.error(f"❌ خطا ({error_count}/{max_errors}): {str(e)[:50]}...")
                time.sleep(5)
            
            if error_count >= max_errors:
                logger.error(f"❌ بیش از {max_errors} خطا رخ داد.")
                break
    
    except KeyboardInterrupt:
        print("\n\n👋 ربات متوقف شد.")

if __name__ == '__main__':
    # بررسی توکن
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ خطا: BOT_TOKEN تنظیم نشده است!")
        print("\n📝 راهنما:")
        print("1. فایل را باز کنید: nano Price.py")
        print("2. خط زیر را پیدا کنید:")
        print('   BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"')
        print("3. توکن خود را جایگزین کنید:")
        print('   BOT_TOKEN = "123456789:ABCdefGHIjk..."')
        print("4. فایل را ذخیره کنید: Ctrl+X -> Y -> Enter")
        print("5. اجرا کنید: python3 Price.py")
        exit(1)
    
    main()
            
