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
import app.user.Keyboards as kb
import app.database.requests as db
from app.user.purchase import is_valid_phone, check_index
from app.user.delivery import get_delivery_mail
from config import MANAGERS_ID


class cart_delivery(StatesGroup):
    cart = State()
    method = State()
    weight = State()
    index = State()
    phone = State()
    fullname = State()
    address = State()
    price_delivery = State()
    days_delivery = State()
    order_id = State()
    cost = State()

    rename_phone = State()
    rename_index = State()
    rename_fullname = State()


R_cart = Router()


async def get_cart_cost_weight(cart):
    total_cost = 0
    total_weight = 0
    for item in cart:
        data = await db.get_product(cart[item]["id"])
        total_cost += data.price * cart[item]["count"]
        total_weight += data.mass * cart[item]["count"]
    return total_cost, total_weight



@R_cart.callback_query(F.data == "open_cart")
async def open_cart(callback: types.CallbackQuery):
    # Удаляем сообщение с фото
    await callback.message.delete()

    user = await db.get_user(callback.from_user.id)
    new_text = f"🛒 Ваша Корзина\n"
    total = 0
    for pid, item in user.cart.items():
        subtotal = item['price'] * item['count']
        total += subtotal
    new_text += f"\n💰 Итого: {total}* ₽"
    new_text += f"\n\n📦 Доставка рассчитывается после оформления."
    keyboard = await kb.get_cart_keyboard(user)
    await callback.message.answer(new_text, reply_markup=keyboard)
    await callback.answer()


@R_cart.callback_query(lambda c: c.data.startswith("plus_cart:"))
async def plus_cart(callback: types.CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    user = await db.get_user(callback.from_user.id)

    # Обновляем количество
    if str(product_id) in user.cart:
        user.cart[str(product_id)]["count"] += 1
        await db.update_cart(user.tg_id, user.cart)

    # Получаем обновленную клавиатуру
    keyboard = await kb.get_cart_keyboard(user)

    # Обновляем текст с новым количеством
    new_text = f"🛒 Ваша Корзина\n"
    total = 0
    for pid, item in user.cart.items():
        subtotal = item['price'] * item['count']
        total += subtotal
    new_text += f"\n💰 Итого: {total}* ₽"
    new_text += f"\n\n📦 Доставка рассчитывается после оформления."

    # Обновляем и текст, и клавиатуру
    await callback.message.edit_text(
        text=new_text,
        reply_markup=keyboard
    )

    await callback.answer(f"Количество увеличено: {user.cart[str(product_id)]['count']} шт")



@R_cart.callback_query(lambda c: c.data.startswith("add_cart:"))
async def open_cart(callback: types.CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    user = await db.get_user(callback.from_user.id)
    product = await db.get_product(product_id)
    cart = user.cart

    product_key = str(product_id)

    if product_key in cart:
        # Увеличиваем количество
        cart[product_key]["count"] += 1
    else:
        # Добавляем новый товар
        cart[product_key] = {
            "name": product.name,
            "price": product.price,  # Не забудьте добавить цену!
            "count": 1,
            "id": product_id
        }
    await db.update_cart(user.tg_id, cart=cart)
    await callback.answer("Товар добавлен в корзину")


@R_cart.callback_query(lambda c: c.data.startswith("minus_cart:"))
async def plus_cart(callback: types.CallbackQuery):
    product_id = int(callback.data.split(":")[1])

    user = await db.get_user(callback.from_user.id)

    text = f"Количество уменьшено: {user.cart[str(product_id)]['count']} шт"
    # Обновляем количество
    if str(product_id) in user.cart:
        user.cart[str(product_id)]["count"] -= 1
        if user.cart[str(product_id)]["count"] == 0:
            user.cart.pop(str(product_id))
            text = "Товар удален из корзины"
        await db.update_cart(user.tg_id, user.cart)

    # Получаем обновленную клавиатуру
    keyboard = await kb.get_cart_keyboard(user)

    # Обновляем текст с новым количеством
    new_text = f"🛒 Ваша Корзина\n"
    total = 0
    for pid, item in user.cart.items():
        subtotal = item['price'] * item['count']
        total += subtotal
    new_text += f"\n💰 Итого: {total}* ₽"
    new_text += f"\n\n📦 Доставка рассчитывается после оформления."

    # Обновляем и текст, и клавиатуру
    await callback.message.edit_text(
        text=new_text,
        reply_markup=keyboard
    )

    await callback.answer(text)


@R_cart.callback_query(lambda c: c.data.startswith("cart_page:"))
async def cart_page(callback: types.CallbackQuery):
    cert_page = int(callback.data.split(":")[1])
    user = await db.get_user(callback.from_user.id)
    keyboard = await kb.get_cart_keyboard(user, cert_page)
    await callback.message.edit_reply_markup(
        reply_markup=keyboard
    )

@R_cart.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    await db.update_cart(callback.from_user.id, {})
    user = await db.get_user(callback.from_user.id)
    await callback.answer("Корзина очищена")
    new_text = """🛒 Ваша Корзина

💰 Итого: 0 ₽"""
    keyboard = await kb.get_cart_keyboard(user)
    await callback.message.edit_text(
        text=new_text,
        reply_markup=keyboard
    )

@R_cart.callback_query(F.data == "place_an_order")
async def place_an_order(callback: types.CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    total_cost, total_weight = await get_cart_cost_weight(user.cart)
    keyboard = await kb.get_cart_delivery(callback.from_user.id, mass=total_weight)
    await callback.message.edit_text("""Выберите тип доставки""", reply_markup=keyboard)


@R_cart.callback_query(lambda c: c.data.startswith("cart_mail:"))
async def cart_mail(callback: types.CallbackQuery, state: FSMContext):
    tg_id = callback.data.split(":")[1]
    user = await db.get_user(tg_id)
    await state.update_data(cart=user.cart,method="mail", cost=None, days_delivery=None)

    await state.set_state(cart_delivery.index)

    await callback.message.edit_text(""" 📮 Введите почтовый индекс получателя

Это 6 цифр, которые вы видите на почтовом отделении или в паспорте

Пример: 101000 (главпочтамт Москвы)""")


@R_cart.message(cart_delivery.index)
async def cart_mail_index(message: Message, state: FSMContext):
    data = await state.get_data()
    if check_index(message.text):
        total_cost, total_weight = await get_cart_cost_weight(data["cart"])
        delivery_data = await get_delivery_mail(mass=total_weight, index_to=message.text)
        await state.update_data(price_delivery=delivery_data["cost"], days_delivery=delivery_data["delivery_days"], index=message.text, cost=total_cost)
        keyboard = await kb.back_to_method(cart=True, tg_id=message.from_user.id)

        text = f"""📦 До вашей почты: {message.text}
💰 Стоимость доставки: {delivery_data["cost"]} руб.
📅 Срок доставки: {delivery_data["delivery_days"]} дней """

        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer("❌ Неверный формат индекса. Пожалуйста, введите индекс в формате 101000.")


@R_cart.callback_query(lambda c: c.data.startswith("phone_cart_for_mail:"))
async def phone_for_cart(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(cart_delivery.phone)
    await callback.message.edit_text("""📱 Введите номер телефона

Формат: +79001234567""")

@R_cart.message(cart_delivery.phone)
async def phone_for_cart_n2(message: Message, state: FSMContext):
    if is_valid_phone(message.text):
        await state.update_data(phone=message.text)

        await message.answer("""⚠️ ВАЖНО! Введите ФИО получателя

Это нужно, чтобы сотрудник почты мог сверить данные с паспортом.
Без совпадения ФИО посылку НЕ ОТДАДУТ.

Формат: Фамилия Имя Отчество
Пример: Иванов Иван Иванович""")

        await state.set_state(cart_delivery.fullname)
    else:
        await state.set_state(cart_delivery.phone)
        await message.answer("❌ Неверный формат номера телефона. Пожалуйста, введите номер в формате +79001234567.")


@R_cart.message(cart_delivery.fullname)
async def quick_purchase_full_name(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    data = await state.get_data()
    await state.set_state(None)
    if data["price_delivery"] == None and data["days_delivery"] == None:
        await message.answer("❌ Неправильно заполнена форма, попробуйте еще раз")
    else:
        order = Order(
            tg_id=message.from_user.id,
            registered=datetime.now(),
            order_data=data["cart"],
            delivery=data["method"],
            phone_number=data["phone"],
            manager=None,
            post_code=data["index"],
            delivery_cost=data["price_delivery"],
            delivery_days=data["days_delivery"],
            cost=data["price_delivery"] + data["cost"],
            status="В обработке",
            order_type="Cost",
            fullname=data["fullname"],
            track_number=None,
            admin_status=None
        )

        order_id = await db.create_order(order)

        await state.update_data(order_id=order_id)

        order_data = await db.get_order(order_id)

        keyboard = await kb.confirmation_order(order_id)
        text_cart = ""
        for item in data['cart']:
            text_cart += f"{data['cart'][item]['name']} - {data['cart'][item]['count']} шт\n"


        await message.answer(f"""📋 Проверь и подтверди заказ:
    
🧸 Товары: {text_cart}
📮 Доставка: {order_data.delivery}
    
📬 Индекс: {order_data.post_code}
    
📞 Телефон: {order_data.phone_number}
    
👤 ФИО: {order_data.fullname}
    
💰 Цена товаров: {data["cost"]}
    
🚚 Доставка: {order_data.delivery_cost}
    
💳 Итого: {order_data.cost}""", reply_markup=keyboard)


async def cart_data_changed(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data["order_id"]

    order_data = await db.get_order(order_id)

    text_cart = ""
    for item in data['cart']:
        text_cart += f"{data['cart'][item]['name']} - {data['cart'][item]['count']} шт\n"

    await message.answer(f"""📋 Проверь и подтверди заказ:

🧸 Товары: {text_cart}
📮 Доставка: {order_data.delivery}

📬 Индекс: {order_data.post_code}

📞 Телефон: {order_data.phone_number}

👤 ФИО: {order_data.fullname}

💰 Цена товаров: {data["cost"]}

🚚 Доставка: {order_data.delivery_cost}

💳 Итого: {order_data.cost}""", reply_markup=await kb.confirmation_order(order_id))


@R_cart.callback_query(lambda c: c.data.startswith("cart_change_data:"))
async def quick_purchase_full_name(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.set_state(None)
    keyboard = await kb.change_order(order_id)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@R_cart.callback_query(lambda c: c.data.startswith("cart_back_order:"))
async def quick_purchase_back_order(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)
    order_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=await kb.confirmation_order(order_id))


@R_cart.callback_query(lambda c: c.data.startswith("cart_rename_phone:"))
async def quick_purchase_change_phone(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(cart_delivery.rename_phone)  # ← Устанавливаем состояние
    await callback.message.edit_text("📱 Введите новый номер телефона (в формате +79001234567):")


@R_cart.callback_query(lambda c: c.data.startswith("cart_rename_index:"))
async def quick_purchase_change_phone(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(cart_delivery.rename_index)  # ← Устанавливаем состояние
    await callback.message.edit_text("📍 Введите новый индекс (в формате 101000):")


@R_cart.callback_query(lambda c: c.data.startswith("cart_rename_fullname:"))
async def quick_purchase_change_phone(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(cart_delivery.rename_fullname)  # ← Устанавливаем состояние
    await callback.message.edit_text("📱 Введите новое ФИО (в формате Фамилия Имя Отчество):")


@R_cart.message(cart_delivery.rename_phone)
async def quick_purchase_change_phone_1(message: Message, state: FSMContext):
    data = await state.get_data()
    if is_valid_phone(message.text):
        await db.update_phone_order(data["order_id"], message.text)
        await state.set_state(None)
        await cart_data_changed(message, state)
    else:
        await message.answer("❌ Неверный формат номера телефона. Пожалуйста, введите номер в формате +79001234567.")


@R_cart.message(cart_delivery.rename_index)
async def quick_purchase_change_phone_1(message: Message, state: FSMContext):
    data = await state.get_data()
    if check_index(message.text):
        await db.update_index_order(data["order_id"], message.text)
        total_cost, total_weight = await get_cart_cost_weight(data["cart"])
        delivery_data = await get_delivery_mail(mass=total_weight, index_to=message.text)
        await db.update_delivery_data_order(data["order_id"], delivery_data["cost"], delivery_data["delivery_days"])
        await state.set_state(None)
        await cart_data_changed(message, state)
    else:
        await message.answer("❌ Неверный формат индекса. Пожалуйста, введите индекс в формате 101000.")


@R_cart.message(cart_delivery.rename_fullname)
async def quick_purchase_change_phone_1(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_fullname_order(data["order_id"], message.text)
    await state.set_state(None)
    await cart_data_changed(message, state)



