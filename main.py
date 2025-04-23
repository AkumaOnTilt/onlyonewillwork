import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
import os

from datetime import datetime  # ⬅️ Добавили

TOKEN = '7622268916:AAFOuwW5P8KZyuec175tvnFPjAtiLX-KYGk'
ADMIN_ID = 7029714670  # <-- Замени на свой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Шаги опроса
class RegForm(StatesGroup):
    par_name = State()
    ch_name = State()
    ch_age = State()
    ch_class = State()
    ch_smena = State()
    ch_eng = State()
    par_numb = State()
    fel_numb = State()


# Создаем БД, если её нет
async def init_db():
    if not os.path.exists("main.db"):
        async with aiosqlite.connect("main.db") as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS test2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    par_name TEXT,
                    ch_name TEXT,
                    ch_age TEXT,
                    ch_class TEXT,
                    ch_smena TEXT,
                    ch_eng TEXT,
                    par_numb TEXT,
                    fel_numb TEXT,
                    id_tg INTEGER,
                    reg_date TEXT
                )
            ''')
            await db.commit()


# Команда /start запускает регистрацию
@dp.message(F.text == "/start")
async def start_registration(message: Message, state: FSMContext):
    await message.answer("Здравствуй! Давай начнем регистрацию.\nНапишите, пожалуйста, свое имя и фамилию:")
    await state.set_state(RegForm.par_name)

@dp.message(RegForm.par_name)
async def step_par_name(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 3:
        await message.answer("❌ Пожалуйста, введите имя корректно.")
        return
    await state.update_data(par_name=message.text)
    await message.answer("Укажите имя и фамилию ребёнка")
    await state.set_state(RegForm.ch_name)

@dp.message(RegForm.ch_name)
async def step_ch_name(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 3:
        await message.answer("❌ Введите имя ребёнка корректно.")
        return
    await state.update_data(ch_name=message.text)
    await message.answer("Укажите возраст ребёнка (только цифры)")
    await state.set_state(RegForm.ch_age)

@dp.message(RegForm.ch_age)
async def step_ch_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите возраст цифрами.")
        return
    await state.update_data(ch_age=message.text)
    await message.answer("Укажите в каком классе учится ребёнок")
    await state.set_state(RegForm.ch_class)

@dp.message(RegForm.ch_class)
async def step_ch_class(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Укажите класс цифрами.")
        return
    await state.update_data(ch_class=message.text)
    await message.answer("Укажите в какую смену учится ребёнок?")
    await state.set_state(RegForm.ch_smena)

@dp.message(RegForm.ch_smena)
async def step_ch_smena(message: Message, state: FSMContext):
    await state.update_data(ch_smena=message.text)
    await message.answer("Как обстоят дела с английским языком у ребенка? Какие оценки? Занимался ли дополнительно?")
    await state.set_state(RegForm.ch_eng)

@dp.message(RegForm.ch_eng)
async def step_ch_eng(message: Message, state: FSMContext):
    await state.update_data(ch_eng=message.text)
    await message.answer("Укажите номер телефона (только цифры)")
    await state.set_state(RegForm.par_numb)

@dp.message(RegForm.par_numb)
async def step_par_numb(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите номер телефона цифрами.")
        return
    await state.update_data(par_numb=message.text)

    # Кнопки-филиалы
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ул Авроры 17/2", callback_data="fil_avrory")],
        [InlineKeyboardButton(text="Ул Революционая,78", callback_data="fil_revol")],
        [InlineKeyboardButton(text="Ул Баландина 2а", callback_data="fil_baland")],
        [InlineKeyboardButton(text="Онлайн-школа", callback_data="fil_online")],
    ])
    await message.answer("В каком филиале вам удобнее заниматься?", reply_markup=kb)
    await state.set_state(RegForm.fel_numb)

@dp.callback_query(F.data.startswith("fil_"))
async def handle_filial(callback: types.CallbackQuery, state: FSMContext):
    filial_map = {
        "fil_avrory": "Ул Авроры 17/2",
        "fil_revol": "Ул Революционая,78",
        "fil_baland": "Ул Баландина 2а",
        "fil_online": "Онлайн-школа"
    }

    choice = filial_map.get(callback.data)
    if not choice:
        await callback.answer("Ошибка выбора филиала.", show_alert=True)
        return

    await state.update_data(fel_numb=choice)
    data = await state.get_data()

    reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ⬅️ Формат даты

    # Сохраняем в БД
    async with aiosqlite.connect("main.db") as db:
        await db.execute('''
            INSERT INTO test2 
            (par_name, ch_name, ch_age, ch_class, ch_smena, ch_eng, par_numb, fel_numb, id_tg, reg_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['par_name'], data['ch_name'], data['ch_age'],
            data['ch_class'], data['ch_smena'], data['ch_eng'],
            data['par_numb'], data['fel_numb'], callback.from_user.id,
            reg_date  # ⬅️ Сохраняем дату
        ))
        await db.commit()

    await callback.message.edit_reply_markup()
    await callback.message.answer(f"{choice}")

    text = (
        f"📥 Новая регистрация:\n\n"
        f"Дата регистрации: {reg_date}\n"
        f"Имя родителя: {data['par_name']}\n"
        f"Имя ребёнка: {data['ch_name']}, {data['ch_age']} лет, {data['ch_class']} класс\n"
        f"Смена ребенка: {data['ch_smena']}\n"
        f"Знания английского: {data['ch_eng']}\n"
        f"Телефон родителя: {data['par_numb']}\n"
        f"Филиал: {data['fel_numb']}\n"
        f"Telegram ID: {callback.from_user.id}"
    )
    await bot.send_message(ADMIN_ID, text)

    await callback.message.answer("✅ Ты успешно зарегистрирован!")
    await state.clear()

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
