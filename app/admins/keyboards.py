from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


import app.database.requests as db

admin_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✉️ Рассылки", callback_data="newsletters"), InlineKeyboardButton(text="📋 Заказы", callback_data="orders_admin")],
                                                 [InlineKeyboardButton(text="📊 Статистика", callback_data="statistics"), InlineKeyboardButton(text="📦 Товары", callback_data="edit_products")],
                                                 [InlineKeyboardButton(text="👥 Пользователи", callback_data="users")]])


admin_products = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Добавить", callback_data="add_product"), InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_product")],
                                                 [InlineKeyboardButton(text="📋 Все товары", callback_data="all_products"), InlineKeyboardButton(text="📦 Товары", callback_data="edit_product")],
                                                 [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_admin")]])


async def edit_product(product_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_description:{product_id}"), InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_price:{product_id}")],
                                                 [InlineKeyboardButton(text="📦 Остаток", callback_data=f"edit_remains:{product_id}"), InlineKeyboardButton(text="📸 Фото", callback_data=f"edit_photo:{product_id}")],
                                                 [InlineKeyboardButton(text="⚙️ Статус",callback_data=f"edit_status:{product_id}"), InlineKeyboardButton(text="📝 Название",callback_data=f"edit_name:{product_id}")],
                                                 [InlineKeyboardButton(text="🔙 Назад", callback_data="all_products")]])
    return keyboard



async def all_products(page: int = 0, buttons_per_page: int = 10) -> InlineKeyboardMarkup:
    total_products = await db.count_all_products()
    all_buttons = []

    # Создаем кнопки асинхронно
    for i in range(1, total_products + 1):
        product = await db.get_product(i)
        all_buttons.append(
            InlineKeyboardButton(text=f"{product.name}", callback_data=f"edit_product:{i}")
        )

    # Вычисляем диапазон для текущей страницы
    start_idx = page * buttons_per_page
    end_idx = start_idx + buttons_per_page

    # Берем кнопки для текущей страницы
    page_buttons = all_buttons[start_idx:end_idx]

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки страницы (по 2 в ряд)
    for i in range(0, len(page_buttons), 2):
        row = page_buttons[i:i + 2]
        builder.row(*row)

    # Добавляем кнопки навигации
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"page_{page - 1}"
        ))

    # Кнопка с номером страницы
    total_pages = (len(all_buttons) + buttons_per_page - 1) // buttons_per_page
    navigation_buttons.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="select_page_list"
    ))

    if end_idx < len(all_buttons):
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"page_{page + 1}"
        ))

    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()


async def confirm_description(product_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Отменить", callback_data=f"edit_product:{product_id}"),
                                                      InlineKeyboardButton(text="✅ Сохранить", callback_data=f"confirm_description:{product_id}")]])
    return keyboard


async def confirm_price(product_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Отменить", callback_data=f"edit_product:{product_id}"),
                                                      InlineKeyboardButton(text="✅ Сохранить", callback_data=f"confirm_price:{product_id}")]])
    return keyboard


async def confirm_remains(product_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Отменить", callback_data=f"edit_product:{product_id}"),
                                                      InlineKeyboardButton(text="✅ Сохранить", callback_data=f"confirm_remains:{product_id}")]])
    return keyboard


async def confirm_name(product_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Отменить", callback_data=f"edit_product:{product_id}"),
                                                      InlineKeyboardButton(text="✅ Сохранить", callback_data=f"confirm_name:{product_id}")]])
    return keyboard


async def confirm_status(product_id):
    builder = InlineKeyboardBuilder()
    product = await db.get_product(product_id)
    buttons = [InlineKeyboardButton(text="⬅️ Отменить", callback_data=f"edit_product:{product_id}")]
    if product.status:
        buttons.append(InlineKeyboardButton(text="🔴 Выключить", callback_data=f"status_switch:{product_id}"))
    else:
        buttons.append(InlineKeyboardButton(text="🟢 Включить", callback_data=f"status_switch:{product_id}"))
    builder.row(*buttons)

    return builder.as_markup()


async def orders(page: int = 0, buttons_per_page: int = 5) -> InlineKeyboardMarkup:
    # Получаем все заказы (теперь это список)
    all_orders = await db.get_all_orders()

    all_buttons = []

    # Создаем кнопки из реальных заказов
    if all_orders:
        for order in all_orders:
            all_buttons.append(
                InlineKeyboardButton(
                    text=f"Заказ #{order.id} | {order.tg_id} | {order.status}",
                    callback_data=f"admin_order:{order.id}"
                )
            )

    builder = InlineKeyboardBuilder()

    # Если заказов нет
    if not all_buttons:
        builder.row(InlineKeyboardButton(text="📦 Нет заказов", callback_data="no_orders"))
        builder.row(InlineKeyboardButton(text="🔙 Назад в админку", callback_data="exit_admin"))
        return builder.as_markup()

    # Вычисляем диапазон для текущей страницы
    start_idx = page * buttons_per_page
    end_idx = start_idx + buttons_per_page

    # Берем кнопки для текущей страницы
    page_buttons = all_buttons[start_idx:end_idx]

    # Добавляем кнопки заказов
    for button in page_buttons:
        builder.row(button)

    # Добавляем кнопки навигации
    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"order_page_{page - 1}"
        ))

    # Кнопка с номером страницы
    total_pages = (len(all_buttons) + buttons_per_page - 1) // buttons_per_page
    navigation_buttons.append(InlineKeyboardButton(
        text=f"Страница {page + 1} из {total_pages}",
        callback_data="select_page_list"
    ))

    if end_idx < len(all_buttons):
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"order_page_{page + 1}"
        ))

    if navigation_buttons:
        builder.row(*navigation_buttons)

    # Добавляем кнопку возврата
    builder.row(InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_panel"))


    return builder.as_markup()