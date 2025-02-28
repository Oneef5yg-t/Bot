from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import sqlite3

# 🔹 ضع توكن البوت هنا
TOKEN = "7710389121:AAF7YjDGH1rxtU4jmt1cWnTnkBl6kwQN2Ag"

# 🔹 تهيئة البوت والتخزين المؤقت للحالات
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# 🔹 إنشاء قاعدة البيانات
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    academic_number TEXT,
    specialization TEXT,
    level TEXT,
    term TEXT
)
""")
conn.commit()

# 🔹 تعريف الحالات لجمع بيانات المستخدم
class Registration(StatesGroup):
    name = State()
    academic_number = State()
    specialization = State()
    level = State()
    term = State()

# ✅ 1. بدء التسجيل عند إدخال /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("مرحبًا! أدخل اسمك الكامل:")
    await Registration.name.set()

# ✅ 2. حفظ الاسم والانتقال للرقم الأكاديمي
@dp.message_handler(state=Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("أدخل رقمك الأكاديمي:")
    await Registration.academic_number.set()

# ✅ 3. حفظ الرقم الأكاديمي وعرض خيارات التخصصات
@dp.message_handler(state=Registration.academic_number)
async def process_academic_number(message: types.Message, state: FSMContext):
    await state.update_data(academic_number=message.text)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("علوم الحاسب", "الهندسة", "الطب", "التجارة")
    await message.reply("اختر تخصصك:", reply_markup=markup)
    await Registration.specialization.set()

# ✅ 4. حفظ التخصص وعرض خيارات المستويات
@dp.message_handler(state=Registration.specialization)
async def process_specialization(message: types.Message, state: FSMContext):
    await state.update_data(specialization=message.text)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("المستوى الأول", "المستوى الثاني", "المستوى الثالث", "المستوى الرابع")
    await message.reply("اختر مستواك الدراسي:", reply_markup=markup)
    await Registration.level.set()

# ✅ 5. حفظ المستوى وعرض خيارات الترم
@dp.message_handler(state=Registration.level)
async def process_level(message: types.Message, state: FSMContext):
    await state.update_data(level=message.text)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("الترم الأول", "الترم الثاني")
    await message.reply("اختر الترم الذي تدرسه:", reply_markup=markup)
    await Registration.term.set()

# ✅ 6. حفظ البيانات النهائية وإنهاء التسجيل
@dp.message_handler(state=Registration.term)
async def process_term(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?)", (
        message.from_user.id,
        user_data['name'],
        user_data['academic_number'],
        user_data['specialization'],
        user_data['level'],
        user_data['term']
    ))
    conn.commit()

    await message.reply("تم التسجيل بنجاح! استخدم القائمة الرئيسية لاختيار الخدمات.", reply_markup=main_menu())
    await state.finish()

# ✅ 7. عرض القائمة الرئيسية للخدمات
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📚 معلومات عن الكلية", "🏫 معلومات عن الجامعة", "👨‍🏫 الدكاترة")
    markup.add("🗺️ خريطة الكلية", "📜 اللوائح والقوانين", "📂 نماذج الاختبارات")
    return markup

@dp.message_handler(lambda message: message.text == "📜 اللوائح والقوانين")
async def show_rules(message: types.Message):
    await message.reply("🔹 هنا تجد جميع اللوائح والقوانين الخاصة بالكلية.")

@dp.message_handler(lambda message: message.text == "📂 نماذج الاختبارات")
async def show_tests(message: types.Message):
    cursor.execute("SELECT specialization, level, term FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if user:
        specialization, level, term = user
        await message.reply(f"📑 إرسال نماذج اختبارات لتخصص {specialization}, {level}, {term}.")
    else:
        await message.reply("❌ لم يتم العثور على بياناتك، أعد التسجيل باستخدام /start.")

# ✅ 8. تشغيل البوت
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)