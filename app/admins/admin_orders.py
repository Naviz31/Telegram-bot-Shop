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