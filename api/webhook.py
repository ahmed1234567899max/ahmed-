import os
import json
import asyncio
import logging
from http.server import BaseHTTPRequestHandler
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from google import genai

# تفعيل السجلات لمراقبة أداء البوت سحابياً
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب المفاتيح الحساسة من متغيرات البيئة السحابية (Vercel Environment Variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# قم بوضع رقم الـ ID الخاص بحسابك التليجرام الشخصي هنا كقيمة افتراضية أو في متغيرات البيئة لكي تصلك السندات عليه
MY_TELEGRAM_ID = int(os.getenv("MY_TELEGRAM_ID", "123456789")) 

# تهيئة تطبيقات التليجرام و Gemini API باستخدام المكتبات الرسمية الحديثة
tg_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# محاكاة لقاعدة بيانات فحص المشتركين (في المشروع الحقيقي يفضل ربطها بـ Supabase أو Firebase)
# لغرض التجربة البداية: حسابك أنت كمدير يتجاوز الدفع دائماً
def is_user_subscribed(user_id):
    return user_id == MY_TELEGRAM_ID

async def process_telegram_update(update_dict: dict):
    """المعالج السحابي الذكي لكل الرسائل والمدفوعات القادمة من تليجرام"""
    try:
        update = Update.de_json(update_dict, tg_app.bot)
        if not update:
            return

        # 1. معالجة الدفع الناجح آلياً بنجوم تليجرام (Automatic Payment)
        if update.message and update.message.successful_payment:
            user = update.message.from_user
            # إرسال رسالة ترحيبية وتأكيدية للعميل فوراً
            await tg_app.bot.send_message(
                chat_id=user.id,
                text="🎉 شكراً لك! تم تفعيل اشتراكك التلقائي عبر النجوم بنجاح.\nيمكنك الآن إرسال الملفات الصوتية والبصمات وتفريغها بلا حدود (باقة الساعة)."
            )
            # إرسال إشعار مالي لك على حسابك الشخصي
            await tg_app.bot.send_message(
                chat_id=MY_TELEGRAM_ID,
                text=f"🔥 اشتراك تلقائي جديد!\n👤 العميل: {user.full_name}\n🆔 الآيدي: `{user.id}`\n🌟 الطريقة: نجوم تليجرام (100 نجمة)"
            )
            return

        # 2. الموافقة التلقائية على فحص الفاتورة قبل الدفع (PreCheckout)
        if update.pre_checkout_query:
            await update.pre_checkout_query.answer(ok=True)
            return

        if not update.message:
            return

        message = update.message
        user_id = message.chat_id

        # 3. استقبال صورة سند التحويل المحلي (الكريمي / القطيبي) من العميل غير المشترك
        if message.photo and not is_user_subscribed(user_id):
            # إنشاء أزرار تحكم تظهر لك أنت فقط في محادثتك الخاصة لتفعيل العميل بنقرة واحدة
            keyboard = [
                [InlineKeyboardButton("✅ تفعيل الاشتراك للعميل", callback_data=f"activate_{user_id}")],
                [InlineKeyboardButton("❌ رفض السند والإشعار", callback_data=f"reject_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # إعادة توجيه السند فوراً إلى حسابك الشخصي على تليجرام
            await tg_app.bot.send_photo(
                chat_id=MY_TELEGRAM_ID,
                photo=message.photo[-1].file_id,
                caption=f"📩 **سند تحويل محلي جديد قيد المراجعة:**\n\n👤 العميل: {message.from_user.full_name}\n🆔 الآيدي: `{user_id}`\n\nتأكد من حسابك البنكي ثم اضغط تفعيل لفتح البوت له.",
                reply_markup=reply_markup
            )
            
            await message.reply_text("⏳ تم استلام صورة السند بنجاح. جاري مراجعته وتطابقه من قبل الإدارة وتفعيل حسابك خلال دقائق معدودة.")
            return

        # 4. معالجة أوامر البوت الأساسية
        if message.text == "/start":
            await message.reply_text(
                f"👋 مرحباً بك {message.from_user.first_name} في بوت التفريغ الصوتي الاحترافي!\n\n"
                "قم بإرسال أي رسالة صوتية (Voice Note) أو ملف صوتي (Audio) "
                "وسأقوم بتحويله إلى نص مكتوب بدقة متناهية وبنفس اللهجة وبدون أي تحريف باستخدام ذكاء Gemini الاصطناعي الحديث."
            )
            return

        # 5. التحقق من حالة اشتراك العميل قبل معالجة ملفه الصوتي
        if (message.voice or message.audio) and not is_user_subscribed(user_id):
            # إظهار أزرار الدفع والتسعيرة المحددة بدقة
            keyboard = [
                [InlineKeyboardButton("🌟 تفعيل فوري تلقائي (100 نجمة)", callback_data="buy_stars")],
                [InlineKeyboardButton("🏦 تحويل محلي (كريمي / قطيبي)", callback_data="local_bank")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text(
                "⚠️ عذراً، الخدمة مدفوعة. يرجى اختيار طريقة الاشتراك وتفعيل رصيدك للبدء في تفريغ ملفك الصوتي:",
                reply_markup=reply_markup
            )
            return

        # 6. تفريغ الملف الصوتي إذا كان العميل مشتركاً (باستخدام gemini-2.5-flash)
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
