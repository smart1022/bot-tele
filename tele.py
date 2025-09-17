import os
import logging
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler

# إعداد اللوجز لمتابعة الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# جلب التوكن من المتغيرات البيئية
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ BOT_TOKEN غير موجود في المتغيرات البيئية")

bot = telegram.Bot(token=TOKEN)

# إنشاء تطبيق Flask
app = Flask(__name__)

# Dispatcher لمعالجة التحديثات
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# دالة عند أمر /start
def start(update, context):
    update.message.reply_text("مرحباً 👋! البوت يعمل الآن ✅")

# دالة عند أي رسالة نصية
def echo(update, context):
    update.message.reply_text(f"أنت كتبت: {update.message.text}")

# إضافة الهاندلرز
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

# مسار رئيسي لاختبار التشغيل
@app.route('/')
def index():
    return "بوت التليجرام شغال ✅"

# مسار الويب هوك من التليجرام
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
