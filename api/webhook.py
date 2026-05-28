import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# إعداد تطبيق Flask
app = Flask(__name__)

# جلب المتغيرات البيئية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# إعداد عميل جيميناي الحديث
ai_client = genai.Client(api_key=GEMINI_KEY)

# بناء تطبيق تليجرام بدون بدء تشغيله كخادم مستقل
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي أي بصمة صوتية أو ملف صوتي وسأقوم بتفريغه وتلخيصه لك فوراً. 🎙️")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_message = await update.message.reply_text("⏳ جاري الاستماع وتفريغ النص الآن...")
    
    try:
        # 1. تحميل الملف الصوتي من تليجرام
        audio_file = await update.message.voice.get_file() if update.message.voice else await update.message.audio.get_file()
        file_bytes = await audio_file.download_as_bytearray()
        
        # 2. إرسال الصوت مباشرة إلى جيميناي لمعالجته وتفريغه
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
        
        # 3. إرسال النتيجة النهائية للمستخدم
        await status_message.edit_text(response.text)
        
    except Exception as e:
        await status_message.edit_text(f"❌ حدث خطأ أثناء معالجة الطلب: {str(e)}")

# ربط الأوامر والرسائل بالكود
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))

@app.route('/api/webhook', methods=['POST'])
def handler():
    # حل مشكلة Event loop is closed في بيئة سحابية مثل Vercel
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        # تشغيل المعالجة بشكل آمن داخل الـ loop الحالي
        loop.run_until_complete(telegram_app.initialize())
        loop.run_until_complete(telegram_app.process_update(update))
        return "OK", 200
    return "Method Not Allowed", 405
        if (message.voice or message.audio) and is_user_subscribed(user_id):
            status_msg = await tg_app.bot.send_message(chat_id=user_id, text="⏳ جاري الاستماع وتفريغ النص الآن...")
            
            audio_file = message.voice if message.voice else message.audio
            file_ext = "ogg" if message.voice else (audio_file.file_name.split('.')[-1] if audio_file.file_name else "mp3")
            
            # مجلد التخزين المؤقت السحابي /tmp
            local_filename = f"/tmp/voice_{audio_file.file_id}.{file_ext}"
            
            # تحميل الملف من تليجرام
            tg_file = await tg_app.bot.get_file(audio_file.file_id)
            await tg_file.download_to_drive(local_filename)

            # رفع ومعالجة الملف عبر عميل جيميناي الحديث
            uploaded_file = ai_client.files.upload(file=local_filename)
            
            prompt_instruction = "قم بتفريغ هذا الملف الصوتي إلى نص مكتوب بدقة متناهية وبنفس اللهجة أو اللغة دون تحريف أو تلخيص"
            
            response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[uploaded_file, prompt_instruction]
            )

            # تعديل رسالة الانتظار وعرض النص النهائي للعميل
            await tg_app.bot.edit_message_text(
                chat_id=user_id, 
                message_id=status_msg.message_id, 
                text=response.text
            )
            
            # تنظيف السيرفر وحذف الملفات فوراً لضمان الخصوصية والأمان
            ai_client.files.delete(name=uploaded_file.name)
            os.remove(local_filename)

    except Exception as e:
        logger.error(f"حدث خطأ أثناء معالجة الطلب: {e}")

    # 7. معالجة نقرات أزرار القائمة (Callback Queries)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # عند اختيار العميل النجوم
        if query.data == "buy_stars":
            await tg_app.bot.send_invoice(
                chat_id=query.message.chat_id,
                title="باقة تفريغ ساعة صوتية",
                description="تفعيل باقة تفريغ 60 دقيقة كاملة بشكل فوري عبر نجوم تليجرام",
                payload="stars_package_100",
                provider_token="", 
                currency="XTR", 
                prices=[LabeledPrice("باقة 1 ساعة", 100)] # سعر النجوم الصارم القاطع
            )
            
        # عند اختيار العميل الدفع المحلي (الكريمي والقطيبي) بـ 1500 ريال
        elif query.data == "local_bank":
            instructions = (
                "🏦 **أسعار الاشتراك وبنية التحويل المحلي:**\n\n"
                "💰 **سعر الباقة:** 1,500 ريال يمني فقط لكل ساعة صوتية.\n\n"
                "يمكنك التحويل الفوري إلى أحد حساباتنا التالية:\n\n"
                "🔹 **بنك الكريمي المميز:**\n"
                " - رقم الحساب: `ضع_رقم_حساب_الكريمي_هنا`\n"
                " - الاسم: [ضع اسمك هنا]\n\n"
                "🔹 **مصرف القطيبي الإسلامي:**\n"
                " - رقم الحساب: `ضع_رقم_حساب_القطيبي_هنا`\n"
                " - الاسم: [ضع اسمك هنا]\n\n"
                "📌 **بعد إتمام التحويل:** قم بأخذ لقطة شاشة واضحة للسند (إشعار إتمام العملية) وأرسلها كصورة مباشرة داخل هذه المحادثة، وسيتم مراجعتها وتفعيل حسابك بلمحة بصر!"
            )
            await tg_app.bot.send_message(chat_id=query.message.chat_id, text=instructions, parse_mode="Markdown")
        
        # أزرار لوحة تحكم الإدارة الخاصة بك (التي تظهر لك تحت صورة السند)
        elif query.data.startswith("activate_"):
            target_user_id = int(query.data.split("_")[1])
            # إشعار العميل بالفتح
            await tg_app.bot.send_message(
                chat_id=target_user_id, 
                text="🎉 أهلاً بك! تم مراجعة وتأكيد سند التحويل المحلي الخاص بك وتفعيل باقة الساعة بنجاح. يمكنك الآن البدء بالاستخدام الفوري وإرسال الصوتيات!"
            )
            # تحديث الرسالة لديك لتأكيد أنك قمت بالضغط وتفعيله
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ **[تم تفعيل العميل بنجاح من قبلك]**")
            
        elif query.data.startswith("reject_"):
            target_user_id = int(query.data.split("_")[1])
            await tg_app.bot.send_message(
                chat_id=target_user_id, 
                text="❌ نعتذر منك، لم يتم تأكيد عملية التحويل. يرجى التأكد من صحة السند والمبلغ المحول أو التواصل مع الدعم الفني."
            )
            await query.edit_message_caption(caption=query.message.caption + "\n\n❌ **[تم رفض السند من قبلك]**")


class handler(BaseHTTPRequestHandler):
    """مستقبل الويب الفوري (Webhook Receiver) المتوافق مع بيئة Vercel Serverless"""
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            update_dict = json.loads(post_data.decode('utf-8'))
            # تشغيل الدالة التزامنية بدون تعطيل السيرفر السحابي
            asyncio.run(process_telegram_update(update_dict))
            
            # إرسال كائن النجاح لتليجرام
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
        except Exception as e:
            logger.error(f"خطأ استقبال الطلب: {e}")
            self.send_response(500)
            self.end_headers()
