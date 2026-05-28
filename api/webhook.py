import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

app = Flask(__name__)

# جلب المتغيرات البيئية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# إعداد عميل جيميناي
ai_client = genai.Client(api_key=GEMINI_KEY)

# بناء تطبيق تليجرام
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا حسام! أرسل لي أي بصمة صوتية أو ملف صوتي وسأقوم بتفريغه فوراً وبدون قيود. 🎙️")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_message = await update.message.reply_text("⏳ جاري الاستماع وتفريغ النص الآن...")
    
    try:
        # تحميل الملف الصوتي من تليجرام
        audio_file = await update.message.voice.get_file() if update.message.voice else await update.message.audio.get_file()
        file_bytes = await audio_file.download_as_bytearray()
        
        # إرسال الصوت مباشرة إلى جيميناي لمعالجته وتفريغه
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                genai.types.Part.from_bytes(
                    data=bytes(file_bytes),
                    mime_type="audio/ogg" if update.message.voice else "audio/mp3"
                ),
                "قم بتفريغ هذا الصوت بدقة وكتابة النص كاملاً مع تنسيقه."
            ]
        )
        
        await status_message.edit_text(response.text)
        
    except Exception as e:
        await status_message.edit_text(f"❌ حدث خطأ أثناء معالجة الطلب: {str(e)}")

# ربط الأوامر
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))

# دالة التشغيل الرئيسية عند استقبال طلب من تليجرام
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        # تشغيل المعالجة بشكل آمن ومستقر في سيرفر Render الدائم
        asyncio.run(telegram_app.initialize())
        asyncio.run(telegram_app.process_update(update))
        return "OK", 200
    return "Method Not Allowed", 405

if __name__ == '__main__':
    # السيرفر سيعمل على المنفذ الذي تحدده المنصة تلقائياً
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
