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


R_admin_order = Router()


@R_admin_order.callback_query(F.data == "orders_admin")
async def orders_admin(callback: CallbackQuery):
    await callback.message.edit_text("""📋 ВСЕ ЗАКАЗЫ

Здесь отображаются все заказы пользователей""", reply_markup=await kb.orders())


@R_admin_order.callback_query(lambda c: c.data.startswith("admin_order:"))
async def admin_order(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = await db.get_order(order_id)
    cart = order.order_data
    order_items = ""
    for item in cart:
        order_items += f"{cart[item]['name']} - {cart[item]['count']} шт. \n"
    if order.delivery == "Почта России":
        deliver_data = f"Почта России\n📦 Индекс: {order.post_code}"

    text = f"""
🧾 НОВЫЙ ЗАКАЗ 

🛍 Состав: 
{order_items}

🚚 Доставка: {deliver_data}  

👤 Клиент: {order.fullname}

⏰ Отправить до: {(datetime.now() + timedelta(days=int(order.delivery_days.split(' - ')[0]))).strftime("%d.%m.%Y")}

📌 Статус: {order.status}

🔄 Требуется обработка
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="orders_admin")]])
    await callback.message.edit_text(text, reply_markup=keyboard)