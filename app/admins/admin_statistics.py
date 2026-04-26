
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
from app.admins.admin_processing import get_data_for_stars


R_statistics = Router()


@R_statistics.callback_query(F.data == "statistics")
async def statistics(callback: CallbackQuery):
    data = await get_data_for_stars()
    text = f"""📊 **Общие показатели:**

━━━━━━━━━━━━━━━━━━━━━
👥 **ПОЛЬЗОВАТЕЛИ**
━━━━━━━━━━━━━━━━━━━━━

👥 Количество подписчиков: {data["users_count"]} 👤
✨ Новые подписчики за сегодня: +{data["new_users"]} 📈
🛍️ Совершенные покупки: {data["paid_orders"]} ✅
🔄 Активные покупки: {data["active_orders"]} ⏳

━━━━━━━━━━━━━━━━━━━━━
📊 **АНАЛИТИКА**
━━━━━━━━━━━━━━━━━━━━━

💵 Общая сумма продаж: {data["amount_orders"]} ₽
📊 Средний чек: {data["average_orders_amount"]} ₽
📆 Заказы за сегодня: {data["today_orders"]} 🎯

━━━━━━━━━━━━━━━━━━━━━
🛒 **ПРОДАЖИ**
━━━━━━━━━━━━━━━━━━━━━

📆 Сегодня: {data["today_orders"]}  ({data["today_revenue"]} ₽)
📈 Неделя: {data["week_orders"]} ({data["week_revenue"]} ₽)
🏆 Месяц: {data["month_orders"]} ({data["month_revenue"]} ₽)
💎 Всего: {data["total_orders"]} ({data["total_revenue"]} ₽)
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="exit_admin")]])
    await callback.message.edit_text(text=text, reply_markup=keyboard)