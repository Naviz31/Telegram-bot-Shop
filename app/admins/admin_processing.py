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





async def get_data_for_stars():
    users_count = await db.count_all_users()
    new_users = await db.get_today_users()
    today_orders = await db.get_today_orders()
    active_orders = await db.get_active_orders_count()
    paid_orders = await db.get_orders_count_payd()
    all_orders = await db.get_orders_count_admin()
    amount_orders, average_orders_amount = await db.get_orders_amount_and_average()


    today_orders, today_revenue = await db.get_orders_amount_admin(1)
    week_orders, week_revenue = await db.get_orders_amount_admin(7)
    month_orders, month_revenue = await db.get_orders_amount_admin(30)
    total_orders, total_revenue = await db.get_orders_amount_admin(0)
    return {"users_count": users_count, "new_users": new_users, "today_orders": today_orders, "active_orders": active_orders, "paid_orders": paid_orders, "amount_orders": amount_orders, "average_orders_amount":average_orders_amount,
            "today_revenue": today_revenue,
            "week_orders": week_orders,"week_revenue": week_revenue,
            "month_orders": month_orders,"month_revenue": month_revenue,
            "total_orders": total_orders,"total_revenue": total_revenue,}