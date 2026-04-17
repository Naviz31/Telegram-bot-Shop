import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, callback_query, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Filter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile, FSInputFile, InputMediaPhoto
from datetime import datetime, timedelta
from aiogram.enums import ParseMode


import app.admins.keyboards as kb
import app.database.requests as db
from config import MANAGERS_ID, ADMINS_ID
from app.managers.order_processing import status_update_notification, notify_user_about_cancellation
from app.users.catalog import IMAGES_DIR


class editproduct(StatesGroup):
    description = State()
    price = State()
    remains = State()
    photo = State()
    status = State()
    name = State()
    product_id = State()

R_admin_product = Router()

@R_admin_product.callback_query(F.data == "edit_products")
async def edit_products(callback: CallbackQuery):
    count_product = await db.count_product()
    remains = await db.count_product_remains(3)
    ended = await db.count_product_remains(0)
    active_products = await db.count_product_active(True)
    disabled_products = await db.count_product_active(False)
    text = f"""📦 Управление товарами

Всего товаров в каталоге: {count_product}
Из них активных: {active_products}
Скрытых / нет в наличии: {disabled_products}

📊 Остатки:
- Заканчиваются (≤ 3 шт.): {remains} товара
- Товаров с нулевым остатком: {ended}"""
    await callback.message.edit_text(text, reply_markup=kb.admin_products)


@R_admin_product.callback_query(lambda c: c.data.startswith("edit_product:"))
async def edit_product(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    product_id = callback.data.split(":")[1]
    product = await db.get_product(product_id)
    image_path = IMAGES_DIR / product.image
    if product.status:
        active_status = "✅ Активен"
    else:
        active_status = "❌ Неактивен"
    text = f"""✏️ **Редактирование:** 

{product.name}

ID: {product.id}
Цена: {product.price} ₽
Остаток: {product.remains} шт.
Статус: {active_status}

Описание: {product.description}

Что меняем?"""
    keyboard = await kb.edit_product(product_id)
    await callback.message.answer_photo(
        photo=FSInputFile(str(image_path)),
        caption=text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML  # ← исправлено: с маленькой буквы
    )
    await callback.answer()


@R_admin_product.callback_query(lambda c: c.data.startswith("page_"))
async def process_page_navigation(callback: callback_query):
    page = int(callback.data.split("_")[1])
    keyboard = await kb.all_products(page=page)  # Добавлен await
    await callback.message.edit_text(
        "📋 Список всех товаров:",
        reply_markup=keyboard
    )
    await callback.answer()


@R_admin_product.callback_query(lambda c: c.data.startswith("all_products"))
async def all_products(callback: CallbackQuery):
    await callback.message.delete()
    keyboard = await kb.all_products(page=0)
    await callback.message.answer(
        "📋 Список всех товаров:",
        reply_markup=keyboard
    )


@R_admin_product.callback_query(lambda c: c.data.startswith("edit_description:"))
async def edit_description(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    product_id = callback.data.split(":")[1]
    product = await db.get_product(product_id)
    await state.set_state(editproduct.description)
    await state.update_data(product_id=product_id)
    text = f"""✏️ Редактирование описания

Товар: {product.name} (ID: {product.id})

📝 Старое описание:
{product.description}

📤 Пришлите новое описание:"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=f"edit_product:{product_id}")]])
    await callback.message.answer(text, reply_markup=keyboard)


@R_admin_product.message(editproduct.description)
async def edit_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()
    product = await db.get_product(data["product_id"])
    await state.set_state(None)
    text = f"""✅ Подтверждение

Товар: {product.name} (ID: {product.id})

📝 Было:
{product.description}

✏️ Стало:
{message.text}

Сохранить новое описание?"""
    keyboard = await kb.confirm_description(product.id)
    await message.answer(text, reply_markup=keyboard)


@R_admin_product.callback_query(lambda c: c.data.startswith("confirm_description:"))
async def confirm_description(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split(":")[1]
    data = await state.get_data()
    await db.update_product_description(product_id, data["description"])
    await state.clear()
    await callback.answer("✅ Описание обновлено")
    await edit_product(callback, state)


@R_admin_product.callback_query(lambda c: c.data.startswith("edit_price:"))
async def edit_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    product_id = callback.data.split(":")[1]
    product = await db.get_product(product_id)
    await state.set_state(editproduct.price)
    await state.update_data(product_id=product_id)
    text = f"""✏️ Редактирование цены

Товар: {product.name} (ID: {product.id})

📝 Старая цена:
{product.price} ₽

📤 Пришлите новую цену:"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=f"edit_product:{product_id}")]])
    await callback.message.answer(text, reply_markup=keyboard)


@R_admin_product.message(editproduct.price)
async def edit_price(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(price=message.text)
        data = await state.get_data()
        product = await db.get_product(data["product_id"])
        await state.set_state(None)
        text = f"""✅ Подтверждение
    
Товар: {product.name} (ID: {product.id})
    
📝 Было:
{product.price} ₽
    
✏️ Стало:
{message.text} ₽
    
Сохранить новую цену?"""
        keyboard = await kb.confirm_price(product.id)
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer("❌ Цена должна быть числом, продолжите ввод")


@R_admin_product.callback_query(lambda c: c.data.startswith("confirm_price:"))
async def confirm_price(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split(":")[1]
    data = await state.get_data()
    await db.update_product_price(product_id, data["price"])
    await state.clear()
    await callback.answer("✅ цена обновлена")
    await edit_product(callback, state)


@R_admin_product.callback_query(lambda c: c.data.startswith("edit_remains:"))
async def edit_remain(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    product_id = callback.data.split(":")[1]
    product = await db.get_product(product_id)
    await state.set_state(editproduct.remains)
    await state.update_data(product_id=product_id)
    text = f"""✏️ Редактирование остатка

Товар: {product.name} (ID: {product.id})

📝 Старый остаток:
{product.remains} шт.

📤 Пришлите новый остаток:"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=f"edit_product:{product_id}")]])
    await callback.message.answer(text, reply_markup=keyboard)


@R_admin_product.message(editproduct.remains)
async def edit_remains(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(remains=message.text)
        data = await state.get_data()
        product = await db.get_product(data["product_id"])
        await state.set_state(None)
        text = f"""✅ Подтверждение

Товар: {product.name} (ID: {product.id})

📝 Было:
{product.remains} шт.

✏️ Стало:
{message.text} шт.

Сохранить новую цену?"""
        keyboard = await kb.confirm_remains(product.id)
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer("❌ Остаток должен быть числом, продолжите ввод")


@R_admin_product.callback_query(lambda c: c.data.startswith("confirm_remains:"))
async def confirm_remains(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split(":")[1]
    data = await state.get_data()
    await db.update_product_remains(product_id, data["remains"])
    await state.clear()
    await callback.answer(f"✅ Остаток обновлен {data['remains']} шт.")
    await edit_product(callback, state)


@R_admin_product.callback_query(lambda c: c.data.startswith("edit_status:"))
async def edit_status(callback: CallbackQuery):
    await callback.message.delete()
    product_id = callback.data.split(":")[1]
    product = await db.get_product(product_id)
    if product.status:
        active = "АКТИВЕН"
        status = "✅ Товар отображается в каталоге и доступен для покупки"
    else:
        active = "НЕАКТИВЕН"
        status = "❌ Товар скрыт из каталога и не доступен для покупки"
    text = f"""📦 Товар: "{product.name}"
🔘 Статус: {active}
{status}

Хотите изменить статус?"""
    await callback.message.answer(text, reply_markup=await kb.confirm_status(product_id))


@R_admin_product.callback_query(lambda c: c.data.startswith("status_switch:"))
async def status_switch(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split(":")[1]
    product = await db.get_product(product_id)
    if product.status:
        await db.update_product_status(product_id, False)
        await callback.answer("❌ Товар скрыт")
    else:
        await db.update_product_status(product_id, True)
        await callback.answer("✅ Товар отображается")
    await edit_product(callback, state)


@R_admin_product.callback_query(lambda c: c.data.startswith("edit_name:"))
async def edit_remain(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    product_id = callback.data.split(":")[1]
    product = await db.get_product(product_id)
    await state.set_state(editproduct.name)
    await state.update_data(product_id=product_id)
    text = f"""✏️ Редактирование названия товара

Товар: {product.name} (ID: {product.id})

📝 Старое название товара:
{product.name} шт.

📤 Пришлите новое название:"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=f"edit_product:{product_id}")]])
    await callback.message.answer(text, reply_markup=keyboard)


@R_admin_product.message(editproduct.name)
async def edit_description(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    product = await db.get_product(data["product_id"])
    await state.set_state(None)
    text = f"""✅ Подтверждение

Товар: {product.name} (ID: {product.id})

📝 Было:
{product.name}

✏️ Стало:
{message.text}

Сохранить новое название товара?"""
    keyboard = await kb.confirm_name(product.id)
    await message.answer(text, reply_markup=keyboard)


@R_admin_product.callback_query(lambda c: c.data.startswith("confirm_name:"))
async def confirm_remains(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split(":")[1]
    data = await state.get_data()
    await db.update_product_name(product_id, data["name"])
    await state.clear()
    await callback.answer(f"✅ Название товара обновлено")
    await edit_product(callback, state)


