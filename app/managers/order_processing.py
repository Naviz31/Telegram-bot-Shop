import asyncio
from pathlib import Path


from aiogram import Router, F, types, Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, callback_query, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.types import InputFile, FSInputFile, InputMediaPhoto
from datetime import datetime


from app.database.models import Product, Order
import app.managers.keyboards as kb
import app.database.requests as db
from config import MANAGERS_ID


async def get_manager_for_order():

    manager_orders = []
    for manager_id in MANAGERS_ID:
        count = await db.get_orders_count(manager_id)
        manager_orders.append((manager_id, count))
    manager_with_fewest = min(manager_orders, key=lambda x: x[1])

    return manager_with_fewest[0]


async def notification_to_the_manager(bot: Bot, order_id: int, manager: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ 🛒 Перейти к заказу", callback_data=f"manager_open_order:{order_id}")]])
    await bot.send_message(chat_id=manager, text=f"Новый заказ №{order_id}", reply_markup=keyboard)


async def status_update_notification(bot: Bot, order_id: int, status: str):
    await db.update_order_status(order_id, status)
    order = await db.get_order(order_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ 🛒 Перейти к заказу", callback_data=f"user_open_order_{order_id}")]])
    await bot.send_message(chat_id=order.tg_id, text=f"""✨ Статус заказа обновлен!

Ваш заказ перешел на новую стадию обработки.

Текущий статус: {order.status}""", reply_markup=keyboard)


async def notify_user_about_cancellation(bot: Bot, order_id: int, reason: str):
    order = await db.get_order(order_id)
    await bot.send_message(chat_id=order.tg_id, text=f"""❌ Статус заказа №{order.id}: Отменен

📋 Причина: {reason}

💳 Средства вернутся на карту автоматически.""")