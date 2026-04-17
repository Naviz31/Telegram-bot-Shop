import asyncio
from pathlib import Path
from datetime import datetime
import re

from aiogram import Router, F, types, Bot
from aiogram.types import Message, callback_query, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.types import InputFile, FSInputFile, InputMediaPhoto
from typing import Union

from config import MANAGERS_ID
from app.database.models import Product, Order
import app.users.keyboards as kb
import app.database.requests as db
from app.users.delivery import get_delivery_mail


class delivery(StatesGroup):
    method = State()
    product = State()
    index = State()
    phone = State()
    fullname = State()
    address = State()
    price_delivery = State()
    days_delivery = State()
    order_id = State()

    rename_phone = State()
    rename_index = State()
    rename_fullname = State()


R_purchase = Router()


def is_valid_phone(phone: str) -> bool:
    # Убираем все лишние символы (пробелы, тире, скобки, плюс)
    digits = re.sub(r'\D', '', phone)

    # Проверяем длину и начало номера
    if len(digits) == 11 and digits[0] in ('7', '8'):
        return True
    elif len(digits) == 10 and digits[0] in ('9', '4', '3', '2', '1', '5', '6', '8'):  # 10 цифр начинается с 9
        return True

    return False

def check_index(index: str) -> bool:
    return len(index) == 6 and index.isdigit()



@R_purchase.callback_query(lambda c: c.data.startswith("quick_purchase:"))
async def quick_purchase(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.update_data(quantity=1)
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    text = f"""🔥 Быстрая покупка 🔥

Вы выбрали товар: {product.name}

Цена: {product.price} руб.

Теперь выберите способ доставки:"""
    keyboard = await kb.get_quick_delivery(product_id)
    await callback.message.answer(text, reply_markup=keyboard)


@R_purchase.callback_query(lambda c: c.data.startswith("quick_mail:"))
async def quick_purchase(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(product=int(callback.data.split(":")[1]))
    await state.update_data(method="Почта России")
    await state.set_state(delivery.index)
    await callback.message.edit_text(""" 📮 Введите почтовый индекс получателя

Это 6 цифр, которые вы видите на почтовом отделении или в паспорте

Пример: 101000 (главпочтамт Москвы)""")


@R_purchase.message(delivery.index)
async def quick_purchase_index(message: Message, state: FSMContext):
    data = await state.get_data()

    if check_index(message.text):

        await state.update_data(index=message.text)
        delivery_data = await get_delivery_mail(product_id=data["product"], index_to=message.text)
        await state.update_data(price_delivery=delivery_data["cost"])
        await state.update_data(days_delivery=delivery_data["delivery_days"])
        keyboard = await kb.back_to_method(product_id=data["product"])

        text = f"""📦 До вашей почты: {message.text}
💰 Стоимость доставки: {delivery_data["cost"]} руб.
📅 Срок доставки: {delivery_data["delivery_days"]} дней """

        await message.answer(text, reply_markup=keyboard)
    else:
        pass  # ДОДЕЛАТЬ!!!


@R_purchase.callback_query(lambda c: c.data.startswith("phone_for_mail:"))
async def quick_purchase(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(delivery.phone)
    await callback.message.edit_text("""📱 Введите номер телефона

Формат: +79001234567""")


@R_purchase.message(delivery.phone)
async def quick_purchase_phone(message: Message, state: FSMContext):
    if is_valid_phone(message.text):
        await state.update_data(phone=message.text)

        await message.answer("""⚠️ ВАЖНО! Введите ФИО получателя

Это нужно, чтобы сотрудник почты мог сверить данные с паспортом.
Без совпадения ФИО посылку НЕ ОТДАДУТ.

Формат: Фамилия Имя Отчество
Пример: Иванов Иван Иванович""")

        await state.set_state(delivery.fullname)
    else:
        await state.set_state(delivery.phone)
        await message.answer("❌ Неверный формат номера телефона. Пожалуйста, введите номер в формате +79001234567.")


@R_purchase.callback_query(lambda c: c.data.startswith("rename_phone:"))
async def quick_purchase_change_phone(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(delivery.rename_phone)  # ← Устанавливаем состояние
    await callback.message.edit_text("📱 Введите новый номер телефона (в формате +79001234567):")


@R_purchase.callback_query(lambda c: c.data.startswith("rename_index:"))
async def quick_purchase_change_phone(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(delivery.rename_index)  # ← Устанавливаем состояние
    await callback.message.edit_text("📍 Введите новый индекс (в формате 101000):")


@R_purchase.callback_query(lambda c: c.data.startswith("rename_fullname:"))
async def quick_purchase_change_phone(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(delivery.rename_fullname)  # ← Устанавливаем состояние
    await callback.message.edit_text("📱 Введите новое ФИО (в формате Фамилия Имя Отчество):")


@R_purchase.message(delivery.rename_phone)
async def quick_purchase_change_phone_1(message: Message, state: FSMContext):
    data = await state.get_data()
    if is_valid_phone(message.text):
        await db.update_phone_order(data["order_id"], message.text)
        await state.set_state(None)
        await data_changed(message, state)
    else:
        await message.answer("❌ Неверный формат номера телефона. Пожалуйста, введите номер в формате +79001234567.")


@R_purchase.message(delivery.rename_index)
async def quick_purchase_change_phone_1(message: Message, state: FSMContext):
    data = await state.get_data()
    if check_index(message.text):
        await db.update_index_order(data["order_id"], message.text)
        delivery_data = await get_delivery_mail(product_id=data["product"], index_to=message.text)
        await db.update_delivery_data_order(data["order_id"], delivery_data["cost"], delivery_data["delivery_days"])
        await state.set_state(None)
        await data_changed(message, state)
    else:
        await message.answer("❌ Неверный формат индекса. Пожалуйста, введите индекс в формате 101000.")


@R_purchase.message(delivery.rename_fullname)
async def quick_purchase_change_phone_1(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_fullname_order(data["order_id"], message.text)
    await state.set_state(None)
    await data_changed(message, state)


@R_purchase.message(delivery.fullname)
async def quick_purchase_full_name(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    data = await state.get_data()
    product_data = await db.get_product(int(data["product"]))
    await state.set_state(None)
    await state.update_data(product=product_data.id)
    order = Order(
        tg_id=message.from_user.id,
        registered=datetime.now(),
        order_data={f"{product_data.id}": {"name": product_data.name, "price": product_data.price, "count": 1, "id": product_data.id}},
        delivery=data["method"],
        phone_number=data["phone"],
        manager=None,
        post_code=data["index"],
        delivery_cost=data["price_delivery"],
        delivery_days=data["days_delivery"],
        cost=int(data["price_delivery"]) + product_data.price,
        status="В обработке",
        order_type="Quick",
        fullname=data["fullname"],
        track_number=None,
        admin_status=None
    )

    order_id = await db.create_order(order)

    await state.update_data(order_id=order_id)

    order_data = await db.get_order(order_id)

    keyboard = await kb.confirmation_order(order_id)

    await message.answer(f"""📋 Проверь и подтверди заказ:

🧸 Товар: {product_data.name}

📮 Доставка: {order_data.delivery}

📬 Индекс: {order_data.post_code}

📞 Телефон: {order_data.phone_number}

👤 ФИО: {order_data.fullname}

💰 Цена товаров: {product_data.price}

🚚 Доставка: {order_data.delivery_cost}

💳 Итого: {order_data.cost}""", reply_markup=keyboard)


@R_purchase.callback_query(lambda c: c.data.startswith("change_data:"))
async def quick_purchase_full_name(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.set_state(None)
    data = await state.get_data()
    product_data = await db.get_product(int(data["product"]))

    order_data = await db.get_order(order_id)
    keyboard = await kb.change_order(order_id)

    await callback.message.edit_text(f"""📋 Проверь и подтверди заказ:

🧸 Товар: {product_data.name}

📮 Доставка: {order_data.delivery}

📬 Индекс: {order_data.post_code}

📞 Телефон: {order_data.phone_number}

👤 ФИО: {order_data.fullname}

💰 Цена товаров: {product_data.price}

🚚 Доставка: {order_data.delivery_cost}

💳 Итого: {order_data.cost}""", reply_markup=keyboard)


async def data_changed(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data["order_id"]
    product_data = await db.get_product(int(data["product"]))

    order_data = await db.get_order(order_id)

    await db.update_cost_order(order_id, (order_data.delivery_cost + product_data.price))

    await message.answer(f"""📋 Проверь и подтверди заказ:

🧸 Товар: {product_data.name}

📮 Доставка: {order_data.delivery}

📬 Индекс: {order_data.post_code}

📞 Телефон: {order_data.phone_number}

👤 ФИО: {order_data.fullname}

💰 Цена товаров: {product_data.price}

🚚 Доставка: {order_data.delivery_cost}

💳 Итого: {order_data.delivery_cost + product_data.price}""", reply_markup=await kb.confirmation_order(order_id))


@R_purchase.callback_query(lambda c: c.data.startswith("back_order:"))
async def quick_purchase_back_order(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)
    order_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=await kb.confirmation_order(order_id))




