import traceback

from dicom_converter.orm import django_orm

import sys
from time import sleep

from django.conf import settings
from yookassa import Payment as YooKassaPayment, Configuration

from apps.converter.models import UserSettings, GlobalSettings
from apps.payments.models import Payment


def update_yookassa_info():
    """
    Обновляем данные о платежах
    поиск по платежам, которые не числятся неоплаченными на нашем сервере
    """
    Configuration.account_id = int(settings.YOOKASSA_SHOP_ID)
    Configuration.secret_key = settings.YOOKASSA_SECRET
    payments = Payment.objects.filter(paid=False).exclude(status__exact='canceled')
    # print(payments)
    prices = GlobalSettings.objects.get(pk=1)

    for payment in payments:
        try:
            yp = YooKassaPayment.find_one(payment.payment_id)  # Получаем данные о платеже
            payment.paid = yp.paid  # Оплачено
            payment.status = yp.status  # Статус платежа
            payment.save()
            if 'succeeded' in payment.status:
                user_info = UserSettings.objects.filter(user=payment.user).last()
                count = user_info.research_avail_count
                if int(payment.amount) == prices.price_1_ru:
                    user_info.research_avail_count = count + 1
                elif int(payment.amount) == prices.price_2_ru:
                    user_info.research_avail_count = count + 5
                elif int(payment.amount) == prices.price_3_ru:
                    user_info.research_avail_count = count + 10
                user_info.save()
                # print(user_info)
                # print(count)
                # print(payment.amount)
                # print(type(payment.amount))
                # print(prices.price_1_ru)
                # print(prices.price_2_ru)
                # print(prices.price_3_ru)
        except:
            print(traceback.format_exc())


if __name__ == '__main__':
    try:
        while True:
            update_yookassa_info()
            sleep(3)
    except KeyboardInterrupt:
        sys.exit(0)
