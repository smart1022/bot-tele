import sqlite3
import os
from dotenv import load_dotenv

# تحميل ملف البيئة
load_dotenv("config.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

print("Loaded Token:", BOT_TOKEN)  # اختبار

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS used_buttons (
        user_id INTEGER,
        button_id INTEGER,
        PRIMARY KEY (user_id, button_id)
    )''')
    conn.commit()

    conn.close()
    print("✅ قاعدة البيانات تم تهيئتها.")


def add_user(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_points(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0


def add_points(user_id, amount):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def record_purchase(user_id, item):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT INTO purchases (user_id, item) VALUES (?, ?)", (user_id, item))
    conn.commit()
    conn.close()


def mark_button_used(user_id, button_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO used_buttons (user_id, button_id) VALUES (?, ?)", (user_id, button_id))
    conn.commit()
    conn.close()


def is_button_used(user_id, button_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM used_buttons WHERE user_id=? AND button_id=?", (user_id, button_id))
    result = c.fetchone()
    conn.close()
    return result is not None


# ⬇️ بيانات وهمية للحسابات
accounts = [
    ('5X', 'حساب A', '100$'),
    ('3X', 'حساب B', '80$'),
    ('10X', 'حساب C', '150$'),
    ('2X', 'حساب D', '60$'),
    ('8X', 'حساب E', '120$'),
    ('1X', 'حساب F', '50$'),
    ('7X', 'حساب G', '110$'),
    ('6X', 'حساب H', '100$'),
    ('4X', 'حساب I', '90$'),
    ('9X', 'حساب J', '130$'),
]


# دالة البدء
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    keyboard = [
        [InlineKeyboardButton("🛒 شراء حسابات باونتي", callback_data='buy_accounts')],
        [
            InlineKeyboardButton("🎯 اربح نقاط", callback_data='earn_points'),
            InlineKeyboardButton("📊 نقاطك", callback_data='your_points'),
        ],
        [InlineKeyboardButton("❓ من هو اراغون", callback_data='who_is_aragon')],
        [
            InlineKeyboardButton("🌐 موقعي سله", url="https://bountyrush-aragon.com/"),
            InlineKeyboardButton("💬 شراء نقاط", url="https://t.me/aragon_opbr"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("أهلاً بك في بوت أراغون 👑\nاختر من الأزرار التالية:", reply_markup=reply_markup)


# عرض الحسابات
async def buy_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []
    for idx, (extreme, account, price) in enumerate(accounts):
        if is_button_used(query.from_user.id, idx):
            price = "غير متوفر"

        if price == "90$":
            price_text = "السلام عليكم"
        elif price == "150$":
            price_text = "عليكم السلام"
        else:
            price_text = price

        row = [
            InlineKeyboardButton(extreme, callback_data=f'extreme_{idx}'),
            InlineKeyboardButton(account, callback_data=f'account_{idx}'),
            InlineKeyboardButton(price_text, callback_data=f'price_{idx}')
        ]
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🛒 قائمة حسابات باونتي المتوفرة:\nاختر ما يناسبك:", reply_markup=reply_markup)


# التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    add_user(user_id)

    if data == 'buy_accounts':
        await buy_accounts(update, context)

    elif data == 'earn_points':
        add_points(user_id, 10)
        await query.edit_message_text("🎉 حصلت على 10 نقاط!")

    elif data == 'your_points':
        points = get_points(user_id)
        await query.edit_message_text(f"📊 نقاطك الحالية: {points} نقطة")

    elif data == 'who_is_aragon':
        await query.edit_message_text("❓ أراغون هو مؤسس باونتي راش في العالم العربي 💥")

    elif data.startswith('price_'):
        idx = int(data.split('_')[1])
        item = accounts[idx]

        record_purchase(user_id, f"{item[1]} - {item[2]}")
        mark_button_used(user_id, idx)

        await query.edit_message_text(
            f"✅ تم تسجيل عملية شراء الحساب {item[1]} بسعر {item[2]}.\nسيتم التواصل معك قريباً."
        )

    else:
        await query.edit_message_text(f"🔘 تم الضغط على: {data}")


# تشغيل البوت
def main():
    init_db()
    print("✅ قاعدة البيانات جاهزة. شغّل البوت الآن...")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
