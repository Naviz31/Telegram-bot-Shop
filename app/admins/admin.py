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



class Admin(Filter):
    async def __call__(self, message: Message):
        return str(message.from_user.id) in ADMINS_ID



R_admin = Router()

@R_admin.message(Admin(), Command("admin"))
async def admin_menu(message: Message):
    await message.answer("Меню Админа", reply_markup=kb.admin_menu)


@R_admin.callback_query(Admin(), F.data == "exit_admin")
async def admin_menu(callback: CallbackQuery):
    await callback.message.edit_text("Меню Админа", reply_markup=kb.admin_menu)




