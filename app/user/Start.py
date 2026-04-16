import asyncio
import aiohttp

from aiogram import Router, F, types, Bot
from aiogram.types import Message, callback_query, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode

import app.user.Keyboards as kb
import app.database.requests as db


user = Router()


@user.message(CommandStart())
async def cmd_start(message: Message):
    start_command = message.text
    referrer = str(start_command[7:])
    if referrer != '' and referrer != str(message.from_user.id):
        await db.set_user(message.from_user.id, message.from_user.username, referral=referrer)
    else:
        await db.set_user(message.from_user.id, message.from_user.username)
    await message.answer("""Добро пожаловать в Магазин""", reply_markup=kb.start_keyboard)