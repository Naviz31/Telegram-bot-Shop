import asyncio
from pathlib import Path

from aiogram import Router, F, types, Bot
from aiogram.types import Message, callback_query, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.types import InputFile, FSInputFile, InputMediaPhoto


from app.database.models import Product
import app.user.Keyboards as kb
import app.database.requests as db


R_catalog = Router()


IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"


async def get_product_text(product: Product):
    return f"""Название: <strong>{product.name}</strong>

цена: {product.price} рублей

Описание: {product.description}"""


@R_catalog.callback_query(F.data == "user_catalog")
async def catalog(callback: types.CallbackQuery):
    await callback.message.delete()

    catalog_data = await db.get_product(1)
    keyboard = await kb.keyboard_catalog(callback.from_user.id, 1)

    # Путь к конкретному файлу (например, "product_1.jpg")
    image_path = IMAGES_DIR / catalog_data.image  # или catalog_data.image если там имя файла

    text = await get_product_text(catalog_data)

    await callback.message.answer_photo(
        photo=FSInputFile(str(image_path)),
        caption=text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML  # ← исправлено: с маленькой буквы
    )
    await callback.answer()

@R_catalog.callback_query(F.data == "add_catalog")
async def add_catalog(callback: types.CallbackQuery):
    product = Product(
    name="Миша",
    image="image1.jpg",  # Список строк
    description="Product description",
    price=100,
    status=True,
    sizes="2x2x2",
    mass=1000
)
    await db.add_product(product)
    await callback.answer("Добавлено")


@R_catalog.callback_query(lambda c: c.data.startswith("catalog_"))
async def catalog_callback(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[1]) # Получаем страницу из данных callback

    keyboard = await kb.keyboard_catalog(callback.from_user.id, page) # Получаем клавиатуру для текущей страницы

    catalog_data = await db.get_product(page)

    image_path = IMAGES_DIR / catalog_data.image # Путь к конкретному фото для товара

    text = await get_product_text(catalog_data) # Текст для товара

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=FSInputFile(str(image_path)),
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=keyboard,
    )
    await callback.answer()