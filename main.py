import os
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from threading import Thread

DATA_FILE = "data/data.json"
TOKEN = os.getenv("BOT_TOKEN") or "TOKENI_BURAYA_YAZ"
ADMIN_IDS = ["7904321871"]

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "last_winner": "Henüz kazanan yok", "draw_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_ref_code(user_id):
    return f"ref{user_id}"

def get_user_by_ref_code(code, data):
    for uid, info in data["users"].items():
        if get_user_ref_code(uid) == code:
            return uid
    return None

data = load_data()
app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name or "Anonim"
    if user_id not in data["users"]:
        data["users"][user_id] = {"username": username, "tickets": 0, "ref": None}
        save_data(data)
    ref_code = context.args[0] if context.args else None
    if ref_code:
        ref_user_id = get_user_by_ref_code(ref_code, data)
        if ref_user_id and ref_user_id != user_id:
            if not data["users"][user_id]["ref"]:
                data["users"][user_id]["ref"] = ref_user_id
                data["users"][ref_user_id]["tickets"] += 1
                data["users"][user_id]["tickets"] += 1
                save_data(data)
    keyboard = [
        [InlineKeyboardButton("🎟 Bilet satın al", callback_data="buy")],
        [InlineKeyboardButton("💰 Ödeme bilgisi", callback_data="pay")],
        [InlineKeyboardButton("🏆 Sıralama tablosu", callback_data="rank")],
        [InlineKeyboardButton("🕒 Sonraki çekiliş", callback_data="next")],
        [InlineKeyboardButton("🎉 Son çekiliş sonucu", callback_data="last")],
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Paneli", callback_data="admin")])
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎉 LordTon'a hoş geldin! Menüyü kullanarak işlemler yapabilirsin.", reply_markup=markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()
    if query.data == "admin" and user_id in ADMIN_IDS:
        total_tickets = sum(u["tickets"] for u in data["users"].values())
        await query.message.reply_text(f"""👑 Admin Paneli
Toplam kullanıcı: {len(data['users'])}
Toplam bilet: {total_tickets}
Son kazanan: {data['last_winner']}""")
    else:
        await query.message.reply_text("✅ İşlem başarılı veya geçersiz komut.")

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

def fake_scheduler():
    while True:
        now = datetime.utcnow()
        if now.hour == 9 and now.minute == 0:
            winner = random.choice(list(data["users"].keys()) or ["7904321871"])
            data["last_winner"] = data["users"][winner]["username"]
            save_data(data)
        import time; time.sleep(60)

Thread(target=fake_scheduler, daemon=True).start()

if __name__ == "__main__":
    app.run_polling()
