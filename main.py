"""
ربات تلگرام "خوشگل آلارم" - نسخه نهایی کامل
قابل اجرا روی Render و Koyeb با پشتیبانی از Flask Web Server
"""

import os
import logging
import json
from typing import Dict
from threading import Thread
from flask import Flask, jsonify

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -------------------- تنظیمات اولیه --------------------
# دریافت توکن از متغیرهای محیطی (امن‌تر)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("توکن ربات پیدا نشد! لطفاً متغیر محیطی BOT_TOKEN را تنظیم کنید.")

# شناسه عددی ادمین (برای دسترسی به /adminpro)
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))  # پیش‌فرض را تغییر دهید

# فعال کردن لاگ برای دیباگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- دیکشنری State کاربران --------------------
user_states: Dict[int, str] = {}
# وضعیت‌های ممکن:
# "WAITING_FOR_NAME" : منتظر اسم (حالت اصلی)
# "WAITING_FOR_CONFIRM" : منتظر آره/اره

# -------------------- فایل آمارگیری --------------------
STATS_FILE = "stats.json"

def load_stats() -> Dict:
    """بارگذاری آمار از فایل"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"total_starts": 0, "users": []}
    return {"total_starts": 0, "users": []}

def save_stats(stats: Dict):
    """ذخیره آمار در فایل"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# -------------------- توابع بررسی ایستراگ‌ها --------------------
def check_easter_eggs(text: str) -> str:
    """
    بررسی ایستراگ‌ها (کلمات مخفی)
    اگر یکی از ایستراگ‌ها پیدا شود، پاسخ مناسب را برمی‌گرداند
    در غیر این صورت None برمی‌گرداند
    """
    text = text.strip()
    
    # 1. بررسی سه بار غزل
    words = text.split()
    if words.count("غزل") == 3 and len(words) == 3:
        return "😵‍💫 آروم‌تر! منم فهمیدم غزل خوشگل‌ترینه!"
    
    # 2. دوستت دارم مهدی
    if text == "دوستت دارم مهدی":
        return "📡 پیام با موفقیت به قلب مهدی ارسال شد. ❤️"
    
    # 3. کی تو رو ساخته؟
    if text in ["کی تو رو ساخته؟", "کی تو رو ساخته"]:
        return "یه برنامه‌نویس که انگار موقع کدنویسی فقط به یک نفر فکر می‌کرد. 😄"
    
    # 4. پایان
    if text == "پایان":
        return "پایان؟ هنوز کلی سورپرایز داخل این ربات قایم شده... 😉\n\nاز مهدی کلمه‌های مخفی رو بپرس، شاید بهت بگه... 🤫"
    
    # 5. راز
    if text == "راز":
        return "پس میخوای یک راز بدونی! 🤫\n\nاین حرف بین خودمون بمونه...\n\nولی من میدونم که مهدی هر وقت به تو فکر میکنه، تو دلش پروانه‌ها شروع به حرکت میکنن. 🦋❤️"
    
    # 6. امشب
    if text == "امشب":
        return "نه فقط امشب...\n\nهر شب یک نفر هست که قبل از خواب به تو فکر میکنه... ❤️"
    
    # 7. رمز ۱
    if text == "رمز ۱":
        return "🔓 تبریک! اولین راز ربات رو پیدا کردی.\n\nراز اول:\n\nمهدی هنوز هم هر وقت تو رو میبینه دست و پاش رو گم میکنه و حرف زدن یادش میره.\n\n(تأثیرات غزله دیگه 🤭)"
    
    # 8. رمز ۲
    if text == "رمز ۲":
        return "نه دیگه 😂\n\nرمزهای دیگه اینقدر ساده نیستن."
    
    # ===== ایستراگ‌های جدید =====
    
    # 9. خوشمزه
    if text == "خوشمزه":
        return "اخ اخ اخ رسیدی به یکی از رمز های مورد علاقه مهدی بهم گفت این رو بهت بگم که تو خوشمزه ترین و گوگولی ترین و ناز ترین و مهربون ترین و خانوم ترین و خوشگل ترین و باشعور ترین و با فهم ترین بامزه ترین و دوست داشتنی ترین هستی… 🥰💕"
    
    # 10. موز
    if text == "موز":
        return "🍌 موز؟ نه، این غزله که از موز هم شیرین‌تره! 🤭"
    
    # 11. دلم تنگ شده
    if text == "دلم تنگ شده":
        return "دلم هم برای تو تنگ شده... 😢\n\nولی میدونی؟ مهدی بیشتر از من دلش برای غزل تنگ شده! 💔"
    
    # 12. مهدی کیه؟
    if text == "مهدی کیه؟":
        return "اون یه آدم خاصه که عاشق غزله! ❤️\n\nبیشتر از این نمیتونم بگم، خودت ازش بپرس! 😉"
    
    # 13. ستاره
    if text == "ستاره":
        return "⭐ ستاره‌ها هم به غزل غبطه میخورن!\n\nچون غزل از همه ستاره‌ها می‌درخشه! ✨\n\nمهدی میگه غزل مثل ستاره‌ای میمونه که توی دل شب می‌درخشه! 🌟❤️"
    
    # 14. رویا
    if text == "رویا":
        return "💭 رویا؟\n\nمهدی همیشه غزل رو توی رویاهای خودش میبینه...\n\nولی میدونی چیه؟ وقتی بیداره، غزل از هر رویایی زیباتره! 🌸\n\n(یادت باشه: بعضی از رویاها به اندازه کافی واقعی هستن که عاشق شی!) ❤️"
    
    # 15. توهم
    if text == "توهم":
        return "🌀 توهم؟ نه بابا!\n\nعشق مهدی به غزل واقعی‌ترین چیزیه که وجود داره!\n\nهمونطور که فیلم فرام میگه: «ایده‌ها مثل ویروس هستن، وقتی به ذهن کسی نفوذ کنن، دیگه نمیشه متوقفشون کرد!»\n\nو عشق مهدی به غزل هم همینه! ❤️"
    
    # 16. ماه کامل
    if text == "ماه کامل":
        return "🌕 ماه کامل رو دیدی؟\n\nحالا غزل رو ببین... میبینی که از ماه کامل هم می‌درخشه! ✨\n\nمهدی میگه ماه کامل یه شب میاد، ولی غزل هر شب توی قلبمه! ❤️"
    
    # 17. ماه
    if text == "ماه":
        return "🌙 ماه؟ نه، این غزله که شب‌ها می‌درخشه!\n\nمهدی میگه ماه کامل هر شب نیست، ولی غزل همیشه توی قلبم هست! ❤️"
    
    # 18. مهتاب
    if text == "مهتاب":
        return "🌙 مهتاب یعنی نور ماه...\n\nولی غزل از مهتاب هم نورانی‌تره! ✨\n\nمهدی میگه مهتاب یه شب می‌درخشه، غزل همیشه! 💕"
    
    # 19. شب
    if text == "شب":
        return "🌃 شب که میشه، ماه کامل میاد...\n\nولی غزل حتی توی تاریک‌ترین شب‌ها هم می‌درخشه! ✨\n\nمهدی میگه غزل نور چشمای منه! ❤️"
    
    # 20. نور
    if text == "نور":
        return "💡 نور؟ ماه کامل هم نور داره...\n\nولی نور غزل از هر نوری قشنگ‌تره! 🌟\n\nمهدی میگه غزل خودش یه ماه کامل تو زمین است! 🌕"
    
    # 21. درخشش
    if text == "درخشش":
        return "✨ درخشش ماه کامل رو دیدی؟\n\nحالا به غزل نگاه کن... می‌بینی که از ماه کامل هم می‌درخشه! \n\nمهدی میگه غزل، ستاره‌ای که ماه رو هم کم‌رنگ میکنه! 🌟❤️"
    
    # 22. بی‌نهایت
    if text == "بی‌نهایت":
        return "♾️ میدونی بی‌نهایت یعنی چی؟\n\nیعنی هر بار که غزل رو میبینم، یه جذابیت جدید توش پیدا میکنم!\n\nانگار هیچوقت تموم نمیشه... همیشه یه چیزی برای شگفت‌زده کردنم داره!\n\nمهدی میگه جذابیت غزل، بی‌نهایته... هر بار که میبینمش، بیشتر عاشق میشم! 😍❤️"
    
    # 23. تموم نشدنی
    if text == "تموم نشدنی":
        return "🌊 جذابیت غزل مثل دریاست... تموم نشدنی!\n\nهر بار که میبینمش، یه عمق جدید توش پیدا میکنم!\n\nانگار هیچوقت به تهش نمیرسم...\n\nمهدی میگه غزل یه اقیانوسه، هر چی بیشتر غرق میشم، بیشتر میخوام غرق بشم! 💕"
    
    # 24. جادو
    if text == "جادو":
        return "🪄 یه جادوی عجیب توی نگاه غزله...\n\nهر بار که میبینمش، یه چیزی جدید کشف میکنم!\n\nانگار هیچوقت تموم نمیشه این جذابیت...\n\nمهدی میگه جادوی غزل، همیشه تازه‌ست و هیچوقت کهنه نمیشه! ✨"
    
    # 25. شگفت‌زده
    if text == "شگفت‌زده":
        return "😲 هر بار که غزل رو میبینم، شگفت‌زده میشم!\n\nانگار هیچوقت عادت نمیکنم به زیباییش...\n\nهر بار یه چیز جدید توش پیدا میکنم که منو متعجب میکنه!\n\nمهدی میگه غزل یه معجزه‌ست که هر بار یه شکلی خودش رو نشون میده! ✨"
    
    # 26. همیشه باش
    if text == "همیشه باش":
        return "💕 هر بار که تورو میبینم، یه جور دیگه جذبت میشم!\n\nهر بار انگار اولین باره میبینمت...\n\nدقیقاً همون احساس رو دارم.\n\nهیچوقت این حجم زیبایی و خانوم بودن برام عادی نمیشه...\n\nو این عالیه.\n\nیه خواهشی ازت دارم...\n\nلطفاً همیشه باش... 🌸❤️"
    
    # 27. لطفا همیشه باش
    if text == "لطفا همیشه باش":
        return "💕 هر بار که تورو میبینم، یه جور دیگه جذبت میشم!\n\nهر بار انگار اولین باره میبینمت...\n\nدقیقاً همون احساس رو دارم.\n\nهیچوقت این حجم زیبایی و خانوم بودن برام عادی نمیشه...\n\nو این عالیه.\n\nیه خواهشی ازت دارم...\n\nلطفاً همیشه باش... 🌸❤️"
    
    # 28. هربار (رمز جدید اضافه شده)
    if text == "هربار":
        return "💕 هر بار که تورو میبینم، یه جور دیگه جذبت میشم!\n\nهر بار انگار اولین باره میبینمت...\n\nدقیقاً همون احساس رو دارم.\n\nهیچوقت این حجم زیبایی و خانوم بودن برام عادی نمیشه...\n\nو این عالیه.\n\nیه خواهشی ازت دارم...\n\nلطفاً همیشه باش... 🌸❤️"
    
    return None

# -------------------- هندلر دستور /start --------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستور /start - شروع ربات و آمارگیری"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "بدون نام"
    
    # ثبت آمار
    stats = load_stats()
    stats["total_starts"] += 1
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
    save_stats(stats)
    
    # تنظیم وضعیت کاربر به حالت انتظار برای اسم
    user_states[user_id] = "WAITING_FOR_NAME"
    
    # ارسال پیام خوش‌آمدگویی
    await update.message.reply_text(
        "به ربات خوشگل آلارم خوش اومدی ❤️\n\n"
        "میدونی زیباترین دختر روی کره زمین کیه؟ 🤔"
    )
    
    logger.info(f"کاربر {username} (ID: {user_id}) ربات را استارت کرد")

# -------------------- هندلر دستور /adminpro --------------------
async def adminpro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستور /adminpro - نمایش آمار استارت‌ها (فقط برای ادمین)"""
    user_id = update.effective_user.id
    
    # بررسی اینکه کاربر ادمین باشد
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ شما دسترسی به این دستور ندارید!")
        return
    
    # دریافت آمار
    stats = load_stats()
    total_starts = stats["total_starts"]
    unique_users = len(stats["users"])
    
    # ارسال آمار
    await update.message.reply_text(
        f"📊 **آمار ربات خوشگل آلارم**\n\n"
        f"🔹 تعداد کل استارت‌ها: {total_starts}\n"
        f"🔹 تعداد کاربران منحصر‌به‌فرد: {unique_users}\n"
        f"🔹 میانگین استارت به ازای هر کاربر: {total_starts / unique_users if unique_users > 0 else 0:.2f}\n\n"
        f"_آخرین به‌روزرسانی: لحظه‌ای_",
        parse_mode="Markdown"
    )
    
    logger.info(f"ادمین (ID: {user_id}) آمار را مشاهده کرد")

# -------------------- هندلر پیام‌های متنی --------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر اصلی پیام‌های متنی - مدیریت منطق ربات"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # **اولویت 1: بررسی ایستراگ‌ها (در هر شرایطی)**
    egg_response = check_easter_eggs(text)
    if egg_response:
        await update.message.reply_text(egg_response)
        return
    
    # **اولویت 2: بررسی وضعیت کاربر**
    state = user_states.get(user_id, "WAITING_FOR_NAME")
    
    if state == "WAITING_FOR_NAME":
        # حالت انتظار برای اسم
        if text == "غزل":
            # پاسخ درست
            user_states[user_id] = "WAITING_FOR_CONFIRM"
            await update.message.reply_text(
                "آفرین، درسته! خیلی باهوشی 😍❤️\n\n"
                "حالا میخوای بدونی چقدر غزل زیباست؟"
            )
        else:
            # پاسخ اشتباه
            await update.message.reply_text(
                "نه، حتی نزدیک هم نشدی! 😄\n"
                "خوشگل‌ترین آدم روی کره زمین قطعاً یکی دیگه‌ست ."
            )
    
    elif state == "WAITING_FOR_CONFIRM":
        # حالت انتظار برای آره/اره
        if text in ["آره", "اره"]:
            # پاسخ مثبت
            user_states[user_id] = "WAITING_FOR_NAME"  # برگشت به حالت اصلی
            await update.message.reply_text(
                "من به عنوان یک ربات نمیتونم این حجم از زیبایی رو بیان کنم. 💔\n"
                "ولی میتونی بری از مهدی بپرسی، اون کامل بهت توضیح میده. 👍"
            )
        else:
            # هر چیز دیگری - دوباره سوال می‌پرسیم
            await update.message.reply_text(
                "خب پس؟ میخوای بدونی چقدر غزل زیباست؟\n"
                "فقط «آره» یا «اره» بگو 😊"
            )

# -------------------- هندلر خطا --------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر خطا - ثبت خطاها در لاگ"""
    logger.error(f"خطا رخ داد: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "متاسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید. 🙏"
        )

# -------------------- وب‌سرور Flask برای Health Check --------------------
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health_check():
    """مسیر Health Check برای جلوگیری از خوابیدن ربات در Render"""
    return jsonify({
        "status": "healthy",
        "bot": "خوشگل آلارم",
        "message": "ربات در حال اجراست! ✅"
    }), 200

@app.route('/stats')
def get_stats():
    """مسیر نمایش آمار (اختیاری)"""
    stats = load_stats()
    return jsonify(stats), 200

def run_flask():
    """اجرای وب‌سرور Flask در یک ترد جداگانه"""
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# -------------------- تابع اصلی --------------------
def main() -> None:
    """تابع اصلی - راه‌اندازی ربات"""
    
    # راه‌اندازی وب‌سرور Flask در ترد جداگانه
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("وب‌سرور Flask راه‌اندازی شد")
    
    # ایجاد اپلیکیشن تلگرام
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ثبت هندلرها
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("adminpro", adminpro_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # ثبت هندلر خطا
    application.add_error_handler(error_handler)
    
    # راه‌اندازی ربات با polling
    logger.info("ربات خوشگل آلارم راه‌اندازی شد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
