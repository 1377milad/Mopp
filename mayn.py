import asyncio
import openai
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# تنظیمات
BOT_TOKEN = "8104124383:AAFrGB8uZmgkRx2EGGMd_H6ldASsLaRQclw"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# تنظیم OpenAI
openai.api_key = OPENAI_API_KEY

# تنظیم لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ذخیره مکالمات کاربران
user_conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام شروع"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    
    welcome_msg = """
🤖 سلام! من یک ربات هوش مصنوعی پیشرفته هستم

قابلیت‌های من:
✅ پاسخ به سوالات شما
✅ نوشتن متن و مقاله
✅ ترجمه متن
✅ برنامه‌نویسی و کد نویسی
✅ حل مسائل ریاضی
✅ خلاصه‌سازی متن
✅ و خیلی چیزهای دیگه!

فقط سوالتون رو بپرسید! 😊

دستورات:
/start - شروع مجدد
/clear - پاک کردن تاریخچه مکالمه
/help - راهنما
    """
    
    await update.message.reply_text(welcome_msg)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک کردن تاریخچه مکالمه"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("✅ تاریخچه مکالمه پاک شد!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنما"""
    help_text = """
🔹 **راهنمای استفاده:**

• فقط سوال یا درخواستتون رو بنویسید
• من به زبان فارسی و انگلیسی پاسخ می‌دم
• می‌تونم کد بنویسم، ترجمه کنم، مسائل حل کنم
• تاریخچه مکالمه رو نگه می‌دارم

🔹 **دستورات:**
/start - شروع مجدد
/clear - پاک کردن تاریخچه
/help - این راهنما

💡 **نکته:** برای بهترین نتیجه، سوالتون رو واضح بپرسید!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def get_ai_response(user_message, conversation_history):
    """دریافت پاسخ از OpenAI"""
    try:
        # ساخت پیام‌های مکالمه
        messages = [
            {"role": "system", "content": "شما یک دستیار هوش مصنوعی مفید، دقیق و دوستانه هستید. به زبان فارسی و انگلیسی پاسخ می‌دهید. اطلاعات به‌روز و دقیق ارائه می‌دهید."}
        ]
        
        # اضافه کردن تاریخچه مکالمه
        for msg in conversation_history:
            messages.append(msg)
        
        # اضافه کردن پیام جدید کاربر
        messages.append({"role": "user", "content": user_message})
        
        # درخواست به OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # یا gpt-4 اگر دسترسی دارید
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"خطا در دریافت پاسخ از OpenAI: {e}")
        return "❌ متأسفانه در حال حاضر مشکلی پیش آمده. لطفاً دوباره تلاش کنید."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # اگر کاربر جدید است
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    # نمایش پیام "در حال تایپ..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # دریافت پاسخ از AI
        ai_response = await get_ai_response(user_message, user_conversations[user_id])
        
        # ذخیره مکالمه
        user_conversations[user_id].append({"role": "user", "content": user_message})
        user_conversations[user_id].append({"role": "assistant", "content": ai_response})
        
        # محدود کردن تاریخچه به 20 پیام آخر
        if len(user_conversations[user_id]) > 20:
            user_conversations[user_id] = user_conversations[user_id][-20:]
        
        # ارسال پاسخ
        if len(ai_response) > 4000:
            # تقسیم پیام‌های طولانی
            chunks = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(ai_response)
            
    except Exception as e:
        logger.error(f"خطا در پردازش پیام: {e}")
        await update.message.reply_text("❌ متأسفانه مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت خطاها"""
    logger.error(f"خطا رخ داد: {context.error}")

def main():
    """راه‌اندازی ربات"""
    # بررسی توکن‌ها
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("❌ لطفاً توکن تلگرام را وارد کنید!")
        return
    
    if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        print("❌ لطفاً API Key OpenAI را وارد کنید!")
        return
    
    # ساخت اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # اضافه کردن error handler
    application.add_error_handler(error_handler)
    
    # راه‌اندازی ربات
    print("🤖 ربات هوش مصنوعی شروع شد...")
    print("✅ آماده دریافت پیام!")
    
    application.run_polling()

if __name__ == '__main__':
    main()


