from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


import app.database.requests as db


managers_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔥 Активные заказы", callback_data="active_orders"),
    InlineKeyboardButton(text="🏁 Завершенные заказы", callback_data="completed_orders")]
])

async def active_orders(tg_id):
    builder = InlineKeyboardBuilder()
    datas = await db.get_active_orders(tg_id)
    for data in datas:
        builder.row(InlineKeyboardButton(text=f"{data.tg_id} - {str(data.registered).split('.')[0]}", callback_data=f"manager_open_order:{data.id}"))
    if not datas:
        builder.row(InlineKeyboardButton(text="У вас пока нет заказов", callback_data="ignore"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_managers_menu"))
    return builder.as_markup()


async def order_settings(order_id):
    builder = InlineKeyboardBuilder()
    order = await db.get_order(order_id)
    buttons_1l = []
    buttons_1l.append(InlineKeyboardButton(text="⚙️ Изменить статус", callback_data=f"manager_status_order:{order_id}"))
    if order.track_number == None:
        buttons_1l.append(InlineKeyboardButton(text="🔢 Добавить трек", callback_data=f"manager_track_order:{order_id}"))
    builder.row(*buttons_1l)
    builder.row(*[InlineKeyboardButton(text="🔥 Завершить заказ", callback_data=f"complete_order:{order_id}"), InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_order:{order_id}")])
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_active_orders"))
    return builder.as_markup()


async def order_status(order_id):
    builder = InlineKeyboardBuilder()
    order = await db.get_order(order_id)
    if order.status == "В обработке":
        builder.row(InlineKeyboardButton(text="Собран", callback_data=f"assembly_order:{order_id}"))
    if order.status == "Собран":
        builder.row(InlineKeyboardButton(text="В пути", callback_data=f"in_transit_order:{order_id}"))
    if order.status == "В пути":
        builder.row(InlineKeyboardButton(text="Доставлен", callback_data=f"delivered_order:{order_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"manager_open_order:{order_id}"))
    return builder.as_markup()


async def order_track(order_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔢 Изменить трек", callback_data=f"manager_track_order:{order_id}"), InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"accept_track:{order_id}")],
                                                     [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_track:{order_id}")]])
    return keyboard

async def order_cancel_YN(order_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 вернуться к заказу", callback_data=f"manager_open_order:{order_id}"), InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_order_Y:{order_id}")]])
    return keyboard