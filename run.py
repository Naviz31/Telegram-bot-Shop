import asyncio
from aiogram import Bot, Dispatcher

from config import TG_TOKEN
from app.database.models import async_main
from app.user.Start import user
from app.user.catalog import R_catalog
from app.user.cart import R_cart
from app.user.purchase import R_purchase
from app.user.payment import R_payment
from app.managers.manager import R_manager

bot = Bot(token=TG_TOKEN)

async def main(bot):
    await async_main()
    dp = Dispatcher()
    dp.include_routers(user, R_catalog, R_cart, R_purchase, R_payment, R_manager)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main(bot))
    except KeyboardInterrupt:
        pass
