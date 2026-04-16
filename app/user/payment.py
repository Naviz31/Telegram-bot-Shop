from aiogram import Router, F, types, Bot
from datetime import date
from aiogram.types import Message, callback_query, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, \
    InlineKeyboardButton
import json
from config import PROVIDER_TOKEN
import app.database.requests as db
from app.managers.order_processing import get_manager_for_order, notification_to_the_manager

R_payment = Router()


@R_payment.callback_query(lambda c: c.data.startswith("confirm_order:"))
async def process_callback_query(callback: types.CallbackQuery, bot: Bot) -> None:
    order_id = callback.data.split(":")[1]

    await callback.answer('')
    description = ''
    order_data = await db.get_order(order_id)

    cart = order_data.order_data
    for item in cart:
        description += f"{cart[item]['name']} - {cart[item]['count']} шт\n"
    description += f"Итого: {order_data.cost} рублей"

    prices = [LabeledPrice(label=f"Оплата заказа №{order_id}", amount=order_data.cost * 100)]

    if prices:
        try:
            await bot.send_invoice(
                chat_id=callback.message.chat.id,
                title=f"Оплата заказа №{order_id}",
                description=description[:255],
                payload=f"order_{order_id}",
                provider_token=PROVIDER_TOKEN,
                currency="RUB",
                prices=prices,
                need_name=False,
                need_phone_number=False,
                need_email=False,
                send_email_to_provider=True,
            )
            await callback.answer("💳 Счёт отправлен!")
        except Exception as e:

            await callback.answer(f"Ошибка: {str(e)[:100]}")


@R_payment.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@R_payment.message(F.successful_payment)
async def process_successful_payment(message: Message) -> None:
    from run import bot
    payload = message.successful_payment.invoice_payload.split("_")[1]
    await db.update_order_admin_status(order_id=payload, status="Active")
    manager = await get_manager_for_order()
    await db.update_order_manager(order_id=payload, manager=manager)
    await notification_to_the_manager(order_id=payload, bot=bot, manager=manager)
    await message.answer(f"""🎉 Готово! Заказ №{payload} оплачен.

Статус заказа можно проверить в разделе «Мои заказы».
Мы уже начали его сборку.""")
