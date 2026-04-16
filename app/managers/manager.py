import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, callback_query, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Filter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta


import app.managers.keyboards as kb
import app.database.requests as db
from config import MANAGERS_ID
from app.managers.order_processing import status_update_notification, notify_user_about_cancellation


class Manager(Filter):
    async def __call__(self, message: Message):
        return str(message.from_user.id) in MANAGERS_ID

class tracking(StatesGroup):
    code = State()
    order_id = State()


class Reason(StatesGroup):
    reason = State()
    order_id = State()


R_manager = Router()

@R_manager.message(Manager(), Command("manager"))
async def manager_menu(message: Message):
    await message.answer("Меню менеджера", reply_markup=kb.managers_menu)


@R_manager.callback_query(F.data == "back_to_managers_menu")
async def manager_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Меню менеджера", reply_markup=kb.managers_menu)


@R_manager.callback_query(F.data.in_(["active_orders", "back_to_active_orders"]))
async def active_orders(callback: CallbackQuery):
    await callback.answer()
    tg_id = callback.from_user.id
    keyboard = await kb.active_orders(tg_id, "Active")
    await callback.message.edit_text("""🔥 Активные заказы 🔥""", reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("accept_order:"))
@R_manager.callback_query(lambda c: c.data.startswith("manager_open_order:"))
async def open_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    order_id = callback.data.split(":")[1]
    await callback.answer()
    order = await db.get_order(order_id)
    cart = order.order_data
    order_items = ""
    for item in cart:
        order_items += f"{cart[item]['name']} - {cart[item]['count']} шт. \n"
    if order.delivery == "Почта России":
        deliver_data = f"Индекс: {order.post_code}"

    text = f"""Состав заказа:
{order_items}
Метод доставки: {order.delivery}

{deliver_data}

Получатель: {order.fullname}

Отправить до: {(datetime.now() + timedelta(int(order.delivery_days.split(' - ')[0]))).strftime("%d.%m.%Y")}

Статус: {order.status}
"""
    keyboard = await kb.order_settings(order_id)
    await callback.message.edit_text(text, reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("manager_status_order:"))
async def status_edit_order(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    keyboard = await kb.order_status(order_id)
    await callback.message.edit_text("Выберите статус заказа", reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("assembly_order:"))
@R_manager.callback_query(lambda c: c.data.startswith("in_transit_order:"))
@R_manager.callback_query(lambda c: c.data.startswith("delivered_order:"))
async def orders_status(callback: CallbackQuery):
    from run import bot
    order_id = callback.data.split(":")[1]
    status = callback.data.split(":")[0]
    if status == "assembly_order":
        status = "Собран"
    elif status == "in_transit_order":
        status = "В пути"
    elif status == "delivered_order":
        status = "Доставлен"
    await status_update_notification(bot, order_id, status)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=f"manager_open_order:{order_id}")]])
    await callback.message.edit_text("Статус заказа изменен на: " + status, reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("manager_track_order:"))
async def track_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(tracking.code)
    await state.update_data(order_id = callback.data.split(":")[1])
    await callback.message.edit_text("Введите трек номер:")


@R_manager.message(tracking.code)
async def track_order_YN(message: Message, state: FSMContext):
    await state.update_data(code = message.text)
    data = await state.get_data()
    keyboard = await kb.order_track(data["order_id"])
    await state.set_state(None)
    await message.answer("Правильно ли введен трек номер к заказу?", reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("accept_track:"))
async def track_order(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split(":")[1]
    data = await state.get_data()
    await db.update_tracking(data["order_id"], data["code"])
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Вернуться к заказу", callback_data=f"manager_open_order:{order_id}")]])
    await callback.message.edit_text("Трек номер добавлен к заказу", reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("cancel_track:"))
async def track_order(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split(":")[1]
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=f"manager_open_order:{order_id}")]])
    await callback.message.edit_text("Добавление трек номера отменено", reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("cancel_order:"))
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split(":")[1]
    await state.update_data(order_id = order_id)
    await state.set_state(Reason.reason)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=f"manager_open_order:{order_id}")]])
    await callback.message.edit_text("""Введите причину отмены заказа
    
Она будет отправлена пользователю:""", reply_markup=keyboard)


@R_manager.message(Reason.reason)
async def cancel_order(message: Message, state: FSMContext):
    await state.update_data(reason = message.text)
    await state.set_state(None)
    data = await state.get_data()
    order_id = data["order_id"]
    await message.answer(f"""Причина отмены: {message.text} 

Отменить заказ?""", reply_markup=await kb.order_cancel_YN(order_id))


@R_manager.callback_query(lambda c: c.data.startswith("cancel_order_Y:"))
async def cancel_order_(callback: CallbackQuery, state: FSMContext):
    from run import bot
    order_id = callback.data.split(":")[1]
    data = await state.get_data()
    reason = data["reason"]
    await notify_user_about_cancellation(bot, order_id, reason)
    await db.update_order_admin_status(order_id = order_id, status = "Canceled")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_managers_menu")]])
    await callback.message.edit_text("Заказ отменен", reply_markup=keyboard)



@R_manager.callback_query(lambda c: c.data.startswith("manager_open_completed_order:"))
async def open_order(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    await callback.answer()
    order = await db.get_order(order_id)
    cart = order.order_data
    order_items = ""
    for item in cart:
        order_items += f"{cart[item]['name']} - {cart[item]['count']} шт. \n"
    if order.delivery == "Почта России":
        deliver_data = f"Индекс: {order.post_code}"

    text = f"""Состав заказа:
{order_items}
Метод доставки: {order.delivery}

{deliver_data}

Получатель: {order.fullname}

Отправить до: {(datetime.now() + timedelta(int(order.delivery_days.split(' - ')[0]))).strftime("%d.%m.%Y")}

Статус: {order.status}
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Возобновить заказ", callback_data=f"activate_order:{order_id}")],
                                                     [InlineKeyboardButton(text="Назад", callback_data="back_to_managers_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("activate_order:"))
async def open_order(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    await callback.answer("Заказ активирован")
    await db.update_order_admin_status(order_id = order_id, status = "Active")
    keyboard = await kb.order_settings(order_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)

@R_manager.callback_query(F.data == "completed_orders")
async def completed_orders(callback: CallbackQuery):
    await callback.answer()
    tg_id = callback.from_user.id
    keyboard = await kb.active_orders(tg_id, "Completed")
    await callback.message.edit_text("""Завершенные заказы""", reply_markup=keyboard)


@R_manager.callback_query(lambda c: c.data.startswith("complete_order:"))
async def cancel_order_(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    await db.update_order_admin_status(order_id = order_id, status = "Completed")
    await db.update_order_status(order_id = order_id, status = "Доставлен")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_managers_menu")]])
    text = f"""Заказ №{order_id} завершен"""
    await callback.message.edit_text(text, reply_markup=keyboard)