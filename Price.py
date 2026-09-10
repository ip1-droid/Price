#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام برای نمایش قیمت‌های لحظه‌ای
طلا، نقره، دلار و یورو
"""

import requests
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# تنظیمات logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ثابت‌های بات
BOT_TOKEN = "8947567937:AAFyt10drJMODWZm3PHQFI-MJzET6bFldNU"  # جایگزین کنید با توکن بات خودتان

# ========== تابع‌های دریافت قیمت‌ها ==========

def get_gold_silver_prices():
    """
    دریافت قیمت طلا و نقره بر اساس تولا ایران
    """
    try:
        # استفاده از API Metal Prices
        response = requests.get(
            'https://api.metals.live/v1/spot/metals',
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # قیمت‌ها به گرم تبدیل می‌شوند
        gold_price = data.get('gold', 0) / 31.1035  # گرم
        silver_price = data.get('silver', 0) / 31.1035  # گرم
        
        return {
            'gold': round(gold_price, 2),
            'silver': round(silver_price, 2),
            'currency': 'USD per gram'
        }
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت طلا و نقره: {e}")
        return None

def get_currency_rates():
    """
    دریافت نرخ دلار و یورو نسبت به ریال
    """
    try:
        # استفاده از API exchangerate-api
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        rates = data.get('rates', {})
        
        # اگر ریال در دسترس نباشد، از یورو استفاده می‌کنیم
        usd_to_eur = rates.get('EUR', 0.85)
        
        # برای نرخ تومانی، از یک منبع دوم استفاده می‌کنیم
        try:
            response2 = requests.get(
                'https://api.exchangerate-api.com/v4/latest/IRR',
                timeout=10
            )
            if response2.status_code == 200:
                data2 = response2.json()
                usd_price = 1 / data2['rates'].get('USD', 1)
            else:
                usd_price = None
        except:
            usd_price = None
        
        return {
            'usd': {
                'value': 1,
                'to_eur': round(usd_to_eur, 4)
            },
            'eur': {
                'value': round(1 / usd_to_eur, 4),
                'to_usd': round(1 / usd_to_eur, 4)
            },
            'updated': datetime.now().strftime('%H:%M:%S')
        }
    except Exception as e:
        logger.error(f"خطا در دریافت نرخ ارز: {e}")
        return None

def get_all_prices():
    """
    دریافت تمام قیمت‌ها
    """
    prices = {}
    
    # دریافت قیمت طلا و نقره
    metals = get_gold_silver_prices()
    if metals:
        prices['metals'] = metals
    
    # دریافت نرخ ارزها
    currencies = get_currency_rates()
    if currencies:
        prices['currencies'] = currencies
    
    return prices

# ========== Handler های تلگرام ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دستور /start
    """
    keyboard = [
        [KeyboardButton("💰 قیمت لحظه‌ای")],
        [KeyboardButton("🥇 طلا و نقره"), KeyboardButton("💵 ارزها")],
        [KeyboardButton("ℹ️ درباره")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_message = """
🤖 به ربات قیمت‌ها خوش آمدید!

من می‌توانم قیمت‌های لحظه‌ای این موارد را برای شما نشان دهم:
    
• 🥇 طلا (بر اساس گرم)
• 🥈 نقره (بر اساس گرم)
• 💵 دلار
• 💶 یورو

از دکمه‌های زیر استفاده کنید:
    """
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def handle_price_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    پردازش درخواست قیمت‌ها
    """
    user_message = update.message.text
    
    # دریافت قیمت‌ها
    prices = get_all_prices()
    
    if user_message == "💰 قیمت لحظه‌ای":
        await send_all_prices(update, prices)
    elif user_message == "🥇 طلا و نقره":
        await send_metals_prices(update, prices)
    elif user_message == "💵 ارزها":
        await send_currency_prices(update, prices)
    elif user_message == "ℹ️ درباره":
        await send_about(update)
    else:
        await update.message.reply_text("لطفاً از دکمه‌های موجود استفاده کنید.")

async def send_all_prices(update: Update, prices: dict):
    """
    نمایش تمام قیمت‌ها
    """
    if not prices:
        await update.message.reply_text("❌ متأسفانه نتوانستم قیمت‌ها را دریافت کنم. بعداً تلاش کنید.")
        return
    
    message = "📊 *قیمت‌های لحظه‌ای*\n\n"
    
    # طلا و نقره
    if 'metals' in prices:
        metals = prices['metals']
        message += f"🥇 *طلا:* ${metals['gold']}/گرم\n"
        message += f"🥈 *نقره:* ${metals['silver']}/گرم\n\n"
    
    # ارزها
    if 'currencies' in prices:
        currencies = prices['currencies']
        message += f"💵 *دلار:* 1 USD = {currencies['eur']['value']:.4f} EUR\n"
        message += f"💶 *یورو:* 1 EUR = {currencies['usd']['value']:.2f} USD\n\n"
        message += f"🕐 *آپدیت:* {currencies['updated']}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def send_metals_prices(update: Update, prices: dict):
    """
    نمایش قیمت طلا و نقره
    """
    if 'metals' not in prices or not prices['metals']:
        await update.message.reply_text("❌ متأسفانه نتوانستم قیمت‌های طلا و نقره را دریافت کنم.")
        return
    
    metals = prices['metals']
    message = f"""
🥇 *قیمت طلا*
💰 ${metals['gold']}/گرم
💰 ${metals['gold'] * 31.1035:.2f}/اونس

🥈 *قیمت نقره*
💰 ${metals['silver']}/گرم
💰 ${metals['silver'] * 31.1035:.2f}/اونس

واحد: {metals['currency']}
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def send_currency_prices(update: Update, prices: dict):
    """
    نمایش نرخ ارزها
    """
    if 'currencies' not in prices or not prices['currencies']:
        await update.message.reply_text("❌ متأسفانه نتوانستم نرخ ارزها را دریافت کنم.")
        return
    
    currencies = prices['currencies']
    message = f"""
💵 *دلار (USD)*
🔄 1 دلار = {currencies['eur']['value']:.4f} یورو

💶 *یورو (EUR)*
🔄 1 یورو = {currencies['usd']['value']:.4f} دلار

🕐 *آپدیت:* {currencies['updated']}

💡 برای نرخ‌های ریالی، لطفاً از منابع رسمی استفاده کنید.
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def send_about(update: Update):
    """
    نمایش اطلاعات درباره
    """
    about_text = """
ℹ️ *درباره این ربات*

🤖 *ربات قیمت‌ها*
نسخه: 1.0

✨ ویژگی‌ها:
• نمایش قیمت لحظه‌ای طلا و نقره
• نمایش نرخ ارزهای رایج
• به‌روزرسانی خودکار
• رابط کاربری ساده و راحت

📊 منابع داده:
• Metal Prices API
• Exchange Rate API

🔗 توجه:
قیمت‌های نمایش‌داده شده برای اطلاع است.
برای معاملات واقعی با منابع رسمی تماس بگیرید.

👨‍💻 ساخته‌شده با پیتون و python-telegram-bot
    """
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    پردازش خطاها
    """
    logger.error(f"خطا: {context.error}")
    if update:
        await update.message.reply_text("❌ خطایی رخ داد. بعداً دوباره تلاش کنید.")

# ========== شروع برنامه ==========

def main():
    """
    نقطه شروع برنامه
    """
    # ایجاد Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    
    # Handler برای پیام‌های متنی
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_price_request
        )
    )
    
    # Handler برای خطاها
    application.add_error_handler(error_handler)
    
    print("✅ ربات در حال اجرا است...")
    print("برای متوقف کردن Ctrl+C را فشار دهید")
    
    # شروع ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
      
