import json
from typing import Optional

from aiogram.fsm.context import FSMContext
from sqlalchemy.engine import connection_memoize
from datetime import datetime, timedelta

from app.database.models import async_session, User, Product, Order
from sqlalchemy import select, update, func, case


def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner

@connection
async def set_user(session, tg_id, name, referral: Optional[str] = None):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))

    if not user:
        session.add(User(tg_id=tg_id, name=name, referral_code=referral, registered=datetime.now()))
        await session.commit()
        return False
    return True if user.name else False



@connection
async def get_product(session, product_id):
    return await session.scalar(select(Product).where(Product.id == product_id))


@connection
async def add_product(session, product):
    session.add(product)
    await session.commit()


@connection
async def count_product(session):
    result = await session.execute(select(func.count(Product.id)))
    count = result.scalar()
    return count


@connection
async def get_user(session, tg_id):
    return await session.scalar(select(User).where(User.tg_id == tg_id))


@connection
async def update_cart(session, tg_id, cart):
    await session.execute(update(User).where(User.tg_id == tg_id).values(cart=cart))
    await session.commit()


@connection
async def create_order(session, order):
    session.add(order)
    await session.commit()
    return order.id


@connection
async def update_active_order(session, order_id, status):
    await session.execute(update(Order).where(Order.id == order_id).values(admin_status=status))
    await session.commit()


@connection
async def get_order(session, order_id):
    return await session.scalar(select(Order).where(Order.id == order_id))


@connection
async def update_index_order(session, order_id, post_code):
    await session.execute(update(Order).where(Order.id == order_id).values(post_code=post_code))
    await session.commit()


@connection
async def update_phone_order(session, order_id, phone_number):
    await session.execute(update(Order).where(Order.id == order_id).values(phone_number=phone_number))
    await session.commit()


@connection
async def update_fullname_order(session, order_id, fullname):
    await session.execute(update(Order).where(Order.id == order_id).values(fullname=fullname))
    await session.commit()


@connection
async def update_cost_order(session, order_id, cost):
    await session.execute(update(Order).where(Order.id == order_id).values(cost=cost))
    await session.commit()


@connection
async def update_delivery_data_order(session, order_id, delivery_cost, delivery_days):
    await session.execute(update(Order).where(Order.id == order_id).values(delivery_cost=delivery_cost, delivery_days=delivery_days))
    await session.commit()


@connection
async def get_orders_count(session, manager):
    result = await session.execute(select(func.count(Order.id)).where((Order.manager == manager) & (Order.admin_status == "Active")))
    count = result.scalar()
    return count


@connection
async def update_order_admin_status(session, order_id, status):
    await session.execute(update(Order).where(Order.id == order_id).values(admin_status=status))
    await session.commit()


@connection
async def update_order_manager(session, order_id, manager):
    await session.execute(update(Order).where(Order.id == order_id).values(manager=manager))
    await session.commit()


@connection
async def get_orders_with_status(session, tg_id, status):
    return await session.scalars(select(Order).where((Order.manager == tg_id) & (Order.admin_status == status)))


@connection
async def update_order_status(session, order_id, status):
    await session.execute(update(Order).where(Order.id == order_id).values(status=status))
    await session.commit()


@connection
async def update_tracking(session, order_id, tracking):
    await session.execute(update(Order).where(Order.id == order_id).values(track_number=tracking))
    await session.commit()


@connection
async def count_product_remains(session, remains):
    query = select(func.count(Product.id)).where(Product.remains <= remains)
    result = await session.execute(query)
    count = result.scalar()
    return count


@connection
async def count_product_active(session, status):
    query = select(func.count(Product.id)).where(Product.status == status)
    result = await session.execute(query)
    count = result.scalar()
    return count


@connection
async def get_all_products(session):
    result = await session.execute(select(Product))
    products = result.scalars().all()
    return products


@connection
async def count_all_products(session):
    query = select(func.count(Product.id))
    result = await session.execute(query)
    count = result.scalar()
    return count


@connection
async def update_product_description(session, product_id, description):
    await session.execute(update(Product).where(Product.id == product_id).values(description=description))
    await session.commit()


@connection
async def update_product_price(session, product_id, price):
    await session.execute(update(Product).where(Product.id == product_id).values(price=price))
    await session.commit()


@connection
async def update_product_remains(session, product_id, remains):
    await session.execute(update(Product).where(Product.id == product_id).values(remains=remains))
    await session.commit()


@connection
async def update_product_status(session, product_id, status):
    await session.execute(update(Product).where(Product.id == product_id).values(status=status))
    await session.commit()


@connection
async def update_product_name(session, product_id, name):
    await session.execute(update(Product).where(Product.id == product_id).values(name=name))
    await session.commit()


@connection
async def get_all_orders(session):
    query = select(Order)
    result = await session.execute(query)
    return result.scalars().all()


@connection
async def count_all_users(session):
    result = await session.execute(select(func.count(User.id)))
    count = result.scalar()
    return count


@connection
async def get_today_users(session):
    today = datetime.today().date()  # Получаем сегодняшнюю дату
    query = select(func.count(User.id)).where(User.registered >= today) \
        .where(User.registered < today + timedelta(days=1))  # Проверяем, что дата регистрации сегодня
    result = await session.execute(query)
    count = result.scalar()  # Получаем результат
    return count


@connection
async def get_today_orders(session):
    today = datetime.today().date()  # Получаем сегодняшнюю дату
    query = select(func.count(Order.id)).where(Order.registered >= today) \
        .where(User.registered < today + timedelta(days=1))  # Проверяем, что дата регистрации сегодня
    result = await session.execute(query)
    count = result.scalar()  # Получаем результат
    return count


@connection
async def get_active_orders_count(session):  # Получаем сегодняшнюю дату
    query = select(func.count(Order.id)).where(Order.admin_status >= "Active")  # Проверяем, что дата регистрации сегодня
    result = await session.execute(query)
    count = result.scalar()  # Получаем результат
    return count


@connection
async def get_orders_count_payd(session):  # Получаем сегодняшнюю дату
    query = select(func.count(Order.id)).where(Order.admin_status != None)  # Проверяем, что дата регистрации сегодня
    result = await session.execute(query)
    count = result.scalar()  # Получаем результат
    return count


@connection
async def get_orders_amount_and_average(session):
    stmt = select(Order).where(Order.admin_status != None)
    result = await session.execute(stmt)
    products = result.scalars().all()
    all_orders = await get_all_orders()
    amount_of_payments = 0
    for order in products:
        amount_of_payments += (order.cost - order.delivery_cost)
    return amount_of_payments, amount_of_payments / len(all_orders)


@connection
async def get_orders_count_admin(session):  # Получаем сегодняшнюю дату
    query = select(func.count(Order.id)) # Проверяем, что дата регистрации сегодня
    result = await session.execute(query)
    count = result.scalar()  # Получаем результат
    return count


@connection
async def get_orders_amount_admin(session, days):
    if days == 0:
        return await get_orders_amount_and_average()
    query = select(Order)
    date = datetime.now() - timedelta(days=days)

    # Добавляем фильтр по дате
    query = query.where(Order.registered >= date)
    query = query.where(Order.registered <= datetime.now())

    # Выполняем запрос
    result = await session.execute(query)
    orders = result.scalars().all()

    # Считаем статистику
    total_orders = len(orders)
    total_amount = sum(order.cost - order.delivery_cost for order in orders)

    return total_orders, total_amount