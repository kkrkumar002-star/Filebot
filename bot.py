import os
import sqlite3
import random
import string
import requests
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID =39325133
API_HASH =908f9506cb6ef3136a106e7e2af9555d "YOUR_API_HASH"
BOT_TOKEN = 8073978123:AAEVxGgXLyjEeZu2c15tYrqB2pYRMuADJvQ "YOUR_BOT_TOKEN"

SHORTLINK_API = "YOUR_SHORTLINK_API" 5ad72e9e34f0cf4b51672fa02efa8ecdd2c09da2
SHORTLINK_URL = "https://ez4short.com/api"

FORCE_CHANNEL ="Hkmoviestudio" "yourchannelusername"
ADMIN_ID = 6484097434  # apna telegram id

app = Client("filebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS files (file_key TEXT, file_id TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS premium (user_id INTEGER, expire_date TEXT)")
db.commit()

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def is_premium(user_id):
    cursor.execute("SELECT expire_date FROM premium WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    if data:
        if datetime.strptime(data[0], "%Y-%m-%d") > datetime.now():
            return True
    return False

@app.on_message(filters.private & filters.document)
async def save_file(client, message):
    file_id = message.document.file_id
    unique_id = generate_id()
    
    cursor.execute("INSERT INTO files VALUES (?,?)", (unique_id, file_id))
    db.commit()

    link = f"https://t.me/{(await client.get_me()).username}?start={unique_id}"
    
    await message.reply_text(f"✅ File Uploaded!\n\n🔗 {link}")

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    db.commit()

    if len(message.command) > 1:
        key = message.command[1]

        cursor.execute("SELECT file_id FROM files WHERE file_key=?", (key,))
        data = cursor.fetchone()

        if data:
            if not is_premium(user_id):
                short_url = requests.get(
                    f"{SHORTLINK_URL}?api={SHORTLINK_API}&url=https://t.me/{(await client.get_me()).username}?start=verify_{key}"
                ).json()["shortenedUrl"]

                await message.reply_text(
                    "📢 Download karne ke liye link open karo:",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Download Now", url=short_url)]]
                    )
                )
            else:
                await client.send_document(message.chat.id, data[0])
        elif key.startswith("verify_"):
            real_key = key.replace("verify_", "")
            cursor.execute("SELECT file_id FROM files WHERE file_key=?", (real_key,))
            file = cursor.fetchone()
            if file:
                msg = await client.send_document(message.chat.id, file[0])
                await msg.delete(delay=600)
    else:
        await message.reply_text("📂 File Upload karo aur earning shuru karo!")

@app.on_message(filters.command("addpremium") & filters.user(ADMIN_ID))
async def add_premium(client, message):
    user_id = int(message.command[1])
    days = int(message.command[2])
    expire = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    cursor.execute("INSERT OR REPLACE INTO premium VALUES (?,?)", (user_id, expire))
    db.commit()

    await message.reply_text("✅ Premium Added")

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(client, message):
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    await message.reply_text(f"👥 Total Users: {users}")

app.run()
