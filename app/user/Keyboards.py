from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import METHOD_SDEK, METHOD_MAIL_RUSSIAN, METHOD_YANDEX

import app.database.requests as db

start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Профиль', callback_data='add_catalog')],
    [InlineKeyboardButton(text='📚 Каталог', callback_data='user_catalog')]
])



async def keyboard_catalog(user_tg_id, page: int = 0) -> InlineKeyboardMarkup:
    total_products = await db.count_product()

    builder = InlineKeyboardBuilder()

    user = await db.get_user(user_tg_id)
    all_buttons = []
    buttons = []

    buttons.append(InlineKeyboardButton(
        text="🛍️ Купить сейчас",
        callback_data=f"quick_purchase:{page}"
    ))
    buttons.append(InlineKeyboardButton(
        text="📦 В корзину",
        callback_data=f"add_cart:{page}"
    ))

    builder.row(*buttons)

    if user.cart:
        all_buttons.append(InlineKeyboardButton(
            text="🛒 В корзине что-то есть",
            callback_data=f"open_cart"
        ))
    else:
        all_buttons.append(InlineKeyboardButton(
            text="🛒 Корзина пуста",
            callback_data=f"open_cart"
        ))
    builder.row(*all_buttons)


    end_idx = total_products
    # Добавляем кнопки навигации
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"catalog_{page - 1}"
        ))

    if total_products > 1:
        total_pages = total_products
        navigation_buttons.append(InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="select_page_list"
        ))

    if page < end_idx:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"catalog_{page + 1}"
        ))

    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


async def get_cart_keyboard(user, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if user.cart:
        # Преобразуем словарь в список для удобства
        cart_items = list(user.cart.items())
        items_per_page = 3
        total_pages = (len(cart_items) + items_per_page - 1) // items_per_page

        # Получаем товары для текущей страницы
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_items = cart_items[start_idx:end_idx]

        # Добавляем товары текущей страницы
        for product_id, product_info in current_items:
            product_data = await db.get_product(product_id)
            subtotal = product_data.price * product_info['count']

            # Кнопка с информацией о товаре
            builder.row(InlineKeyboardButton(
                text=f"{product_info['name']} - {subtotal} ₽",
                callback_data="ignore"
            ))

            # Кнопки управления количеством
            buttons = [
                InlineKeyboardButton(text="➕", callback_data=f"plus_cart:{product_id}"),
                InlineKeyboardButton(text=f"{product_info['count']}", callback_data="ignore"),
                InlineKeyboardButton(text="➖", callback_data=f"minus_cart:{product_id}")
            ]
            builder.row(*buttons)

        # Пагинация (если больше одной страницы)
        if total_pages > 1:
            nav_buttons = []

            # Кнопка "Назад"
            if page > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"cart_page:{page - 1}"
                ))


            nav_buttons.append(InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="ignore"
            ))

            # Кнопка "Вперед"
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text="Вперед ▶️",
                    callback_data=f"cart_page:{page + 1}"
                ))

            builder.row(*nav_buttons)

        # Кнопка очистки корзины
        builder.row(InlineKeyboardButton(
            text="🗑️ Очистить корзину",
            callback_data="clear_cart"
        ))

    else:
        # Пустая корзина
        builder.row(InlineKeyboardButton(
            text="🛒 Корзина пуста",
            callback_data="ignore"
        ))

    if user.cart:
        builder.row(InlineKeyboardButton(
            text="💳 Оформить заказ",
            callback_data="place_an_order"
        ))

    # Кнопка возврата в каталог
    builder.row(InlineKeyboardButton(
        text="🛍️ Вернуться к каталогу",
        callback_data="catalog_1"
    ))

    return builder.as_markup()



async def get_quick_delivery(product_id):
    builder = InlineKeyboardBuilder()
    buttons = []

    if METHOD_MAIL_RUSSIAN:
        buttons.append(InlineKeyboardButton(
            text="📬 Почта России",
            callback_data=f"quick_mail:{product_id}"
        ))
    if METHOD_YANDEX:
        buttons.append(InlineKeyboardButton(
            text="🚚 Курьер",
            callback_data=f"quick_courier:{product_id}"
        ))
    if METHOD_SDEK:
        buttons.append(InlineKeyboardButton(
            text="📦 СДЭК",
            callback_data=f"quick_sdek:{product_id}"
        ))

    builder.row(*buttons)
    builder.row(InlineKeyboardButton(
            text="🙋‍♂️ Самовывоз",
            callback_data=f"quick_pickup:{product_id}"
        ))
    return builder.as_markup()


async def get_cart_delivery(tg_id, mass=0):
    builder = InlineKeyboardBuilder()
    buttons = []

    if METHOD_MAIL_RUSSIAN and mass < 5000:
        buttons.append(InlineKeyboardButton(
            text="📬 Почта России",
            callback_data=f"cart_mail:{tg_id}"
        ))
    if METHOD_YANDEX:
        buttons.append(InlineKeyboardButton(
            text="🚚 Курьер",
            callback_data=f"cart_courier:{tg_id}"
        ))
    if METHOD_SDEK:
        buttons.append(InlineKeyboardButton(
            text="📦 СДЭК",
            callback_data=f"cart_sdek:{tg_id}"
        ))

    builder.row(*buttons)
    builder.row(InlineKeyboardButton(
        text="🙋‍♂️ Самовывоз",
        callback_data=f"cart_pickup:{tg_id}"
    ))
    return builder.as_markup()

async def back_to_method(product_id = None, cart=False, tg_id=None):
    builder = InlineKeyboardBuilder()
    if cart:
        builder.row(*[InlineKeyboardButton(text="🔙 Назад", callback_data=f"place_an_order")],
                    InlineKeyboardButton(text="Далее", callback_data=f"phone_cart_for_mail:{tg_id}"))
    else:
        builder.row(*[InlineKeyboardButton(text="🔙 Назад", callback_data=f"quick_purchase:{product_id}")], InlineKeyboardButton(text="Далее", callback_data=f"phone_for_mail:{product_id}"))
    return builder.as_markup()


async def confirmation_order(order_id):
    builder = InlineKeyboardBuilder()
    data = await db.get_order(order_id)
    print(f"🔍 confirmation_order: order_id={order_id}, order_type={data.order_type}")  # 👈 ДОБАВЬТЕ

    if data.order_type == "Quick":
        callback_data = f"confirm_order:{order_id}"
        print(f"🔍 Создаю кнопку для Quick с callback: {callback_data}")  # 👈 ДОБАВЬТЕ
        builder.row(InlineKeyboardButton(text="✏️ Изменить", callback_data=f"change_data:{order_id}"))
        builder.row(InlineKeyboardButton(text="💳 Перейти к оплате", callback_data=callback_data))
    else:
        callback_data = f"confirm_order:{order_id}"
        print(f"🔍 Создаю кнопку для Cost с callback: {callback_data}")  # 👈 ДОБАВЬТЕ
        builder.row(InlineKeyboardButton(text="✏️ Изменить", callback_data=f"cart_change_data:{order_id}"))
        builder.row(InlineKeyboardButton(text="💳 Перейти к оплате", callback_data=callback_data))

    return builder.as_markup()

async def change_order(order_id):
    builder = InlineKeyboardBuilder()
    order = await db.get_order(order_id)
    if order.order_type == "Quick":
        builder.row(InlineKeyboardButton(text="✏️ Что вы хотите изменить?", callback_data=f"ignore"))
        builder.row(*[InlineKeyboardButton(text="🚚 Способ доставки", callback_data=f"ignore"), InlineKeyboardButton(text="📬 Индекс", callback_data=f"rename_index:{order_id}:")])
        builder.row(*[InlineKeyboardButton(text="📱 Номер телефона", callback_data=f"rename_phone:{order_id}"),
                      InlineKeyboardButton(text="👤 ФИО", callback_data=f"rename_fullname:{order_id}")])
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_order:{order_id}"))
    else:
        builder.row(InlineKeyboardButton(text="✏️ Что вы хотите изменить?", callback_data=f"ignore"))
        builder.row(*[InlineKeyboardButton(text="🚚 Способ доставки", callback_data=f"ignore"), InlineKeyboardButton(text="📬 Индекс", callback_data=f"cart_rename_index:{order_id}:")])
        builder.row(*[InlineKeyboardButton(text="📱 Номер телефона", callback_data=f"cart_rename_phone:{order_id}"),
                      InlineKeyboardButton(text="👤 ФИО", callback_data=f"cart_rename_fullname:{order_id}")])
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"cart_back_order:{order_id}"))
    return builder.as_markup()