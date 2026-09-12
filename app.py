import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

# កំណត់ការមើល Log
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = "8916432999:AAHIUc0O_a0dTfNbGvMYoRvWfuJG47alVE8"

# មុខងារពេលចាប់ផ្ដើម /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    welcome_text = (
        f"សួស្តី {user_name}! 🙏\n\n"
        "ខ្ញុំជា Playlist Manager Bot សម្រាប់ទាញយកវីដេអូ និងអូឌីយ៉ូ ពី YouTube និង TikTok ក្នុងកម្រិតច្បាស់បំផុត (Full Quality)\n\n"
        "👉 **វិធីប្រើប្រាស់៖** សូមផ្ញើលីង (URL) វីដេអូ ឬ Playlist របស់អ្នកចូលមកទីនេះបាន!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# ទទួលលីងពីអ្នកប្រើប្រាស់រួចបង្ហាញ Menu ឲ្យរើស Format
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("❌ សូមផ្ញើលីង (URL) ដែលត្រឹមត្រូវមក!")
        return

    # រក្សាទុក URL ក្នុង context ដើម្បីយកទៅប្រើពេលចុចបូតុង
    context.user_data['target_url'] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 MP4 (កម្រិតវីដេអូខ្ពស់បំផុត)", callback_data="download_mp4"),
            InlineKeyboardButton("🎵 MP3 (កម្រិតអូឌីយ៉ូខ្ពស់បំផុត)", callback_data="download_mp3")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔗 បានទទួលលីងរបស់អ្នកហើយ! តើអ្នកចង់ទាញយកជាទម្រង់អ្វីដែរ?", reply_markup=reply_markup)

# មុខងារទាញយកនិងបំលែងតាមការចុចបូតុង (Callback Query)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('target_url')
    if not url:
        await query.edit_message_text("⚠️ រកមិនឃើញលីងរបស់អ្នកទេ សូមផ្ញើលីងម្តងទៀត។")
        return

    choice = query.data
    await query.edit_message_text("⏳ កំពុងដំណើរការទាញយក និងបំលែងឯកសារ សូមរង់ចាំបន្តិច...")

    output_file = None
    try:
        if choice == "download_mp4":
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
            }
        elif choice == "download_mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'outtmpl': '%(title)s.%(ext)s',
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            output_file = ydl.prepare_filename(info)
            if choice == "download_mp3":
                output_file = os.path.splitext(output_file)[0] + ".mp3"

        await query.edit_message_text("📤 កំពុងបញ្ជូនឯកសារទៅកាន់ Telegram...")
        with open(output_file, 'rb') as f:
            if choice == "download_mp3":
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f)
            else:
                await context.bot.send_video(chat_id=query.message.chat_id, video=f)
        
        await query.message.reply_text("✅ ការទាញយកបានជោគជ័យ!")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await query.message.reply_text(
            "⚠️ **បតកំពុងជួបបញ្ហា!**\n\n"
            "មិនអាចទាញយកលីងនេះបានទេ វាអាចបណ្តាលមកពីលីងមិនត្រឹមត្រូវ ឬមានបញ្ហាបច្ចេកទេសពីប្រភពវីដេអូ។\n"
            f"รายละเอียด Error: `{str(e)}`",
            parse_mode="Markdown"
        )

    finally:
        if output_file and os.path.exists(output_file):
            os.remove(output_file)

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

if __name__ == "__main__":
    main()
    