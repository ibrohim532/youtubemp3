import os
import sqlite3
import yt_dlp
import imageio_ffmpeg
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================== SOZLAMALAR ==================
TOKEN = "8625632669:AAFVYzxSL2brfdoux8UpeV78TK3IK55DnCk"
ADMIN_ID = 8578660273       # Sizning Telegram ID
CHANNEL_USERNAME = "@everest_kids"  # Kanal faqat info uchun
# ================================================

# ================== DATABASE ====================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    conn.commit()

def user_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]
# ================================================

# ================== OBUNA TEKSHIRUVI ==================
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hozircha har doim True qaytaramiz (obuna tekshiruvini o'zingiz qo'shishingiz mumkin)
    return True
# =======================================================

# ================== FUNKSIYALAR =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)
    await update.message.reply_text("🎵 Qo'shiq nomi yoki YouTube link yuboring!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["query"] = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3", callback_data="mp3"),
            InlineKeyboardButton("🎬 Video", callback_data="video")
        ]
    ]

    await update.message.reply_text(
        "Qaysi format kerak?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    search_query = context.user_data.get("query")
    await query.edit_message_text("⏳ Yuklanmoqda...")

    # imageio-ffmpeg orqali avtomatik ffmpeg path olish
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    if query.data == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'music.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': ffmpeg_path,
            'quiet': True,
            'no_warnings': True,
        }
    else:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s',
            'ffmpeg_location': ffmpeg_path,
            'quiet': True,
            'no_warnings': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{search_query}"])

        if query.data == "mp3":
            await query.message.reply_audio(open("music.mp3", "rb"))
            os.remove("music.mp3")
        else:
            # Video formati har doim mp4 emas, shuning uchun fayl kengaytmasini aniqlashimiz kerak
            # Osonroq bo'lishi uchun video faylni qidiramiz
            video_file = None
            for file in os.listdir():
                if file.startswith("video.") and os.path.isfile(file):
                    video_file = file
                    break

            if video_file:
                await query.message.reply_video(open(video_file, "rb"))
                os.remove(video_file)
            else:
                await query.message.reply_text("❌ Video fayl topilmadi!")

    except Exception as e:
        await query.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")

# ================== ADMIN =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        count = user_count()
        await update.message.reply_text(f"👥 Foydalanuvchilar soni: {count}")
    else:
        await update.message.reply_text("❌ Siz admin emassiz!")
# ================================================

# ================== BOTNI ISHGA TUSHURISH ==========
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot ishga tushdi...")
    app.run_polling()