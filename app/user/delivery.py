from pochta import Delivery
from typing import Dict, Any, Tuple
from pochta.enums import MailCategory, MailType
from config import INDEX_FROM, LOGIN_MAIL, PASSWORD_MAIL, TOKEN_MAIL
import app.database.requests as db


async def get_delivery_mail(index_to, product_id = None, mass = None) -> Dict[str, Any]:
    """
    Асинхронная функция расчета стоимости и времени доставки
    """
    if product_id:
        product = await db.get_product(product_id)
        mass = product.mass
    try:
        delivery = Delivery(LOGIN_MAIL, PASSWORD_MAIL, TOKEN_MAIL)
        calc_result = delivery.nogroup.calc_delivery_rate(
                index_from=INDEX_FROM,
                index_to=index_to,
                mail_category=MailCategory.SIMPLE,  # ← Самое главное: меняем на SIMPLE
                mail_type=MailType.BANDEROL,  # ← Бандероль (дешевле посылки)
                mass=mass,  # Вес в граммах
                fragile=False,  # ← Хрупкость удорожает
        )
        delivery_time = calc_result.get('delivery-time', {})
        return {
            'cost': calc_result.get('total-rate', 0) // 100,
            'delivery_days': f"{delivery_time.get('min-days', 0)+2} - {delivery_time.get('max-days', 0) + 2}"
        }

    except Exception as e:
        print(f"Ошибка: {e}")
        return {'cost': 0, 'delivery_days_min': 0, 'delivery_days_max': 0}
