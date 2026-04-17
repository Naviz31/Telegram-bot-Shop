import asyncio
from aiogram import Bot, Dispatcher

from config import TG_TOKEN
from app.database.models import async_main
from app.users.Start import user
from app.users.catalog import R_catalog
from app.users.cart import R_cart
from app.users.purchase import R_purchase
from app.users.payment import R_payment
from app.managers.manager import R_manager
from app.admins.admin import R_admin
from app.admins.admin_products import R_admin_product
from app.admins.admin_orders import R_admin_order


bot = Bot(token=TG_TOKEN)

async def main(bot):
    await async_main()
    dp = Dispatcher()
    dp.include_routers(user, R_catalog, R_cart, R_purchase, R_payment, R_manager, R_admin, R_admin_product, R_admin_order)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main(bot))
    except KeyboardInterrupt:
        pass
