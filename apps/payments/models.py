from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    """Модель платежа."""

    amount = models.DecimalField(_('Сумма'), max_digits=10, decimal_places=2, )
    description = models.CharField(_('Описание'), max_length=255, )
    payment_id = models.CharField(_('ID платежа YooKassa'), max_length=255, blank=True, )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True, )
    paid = models.BooleanField(_('Оплачено'), default=False, )
    status = models.CharField(_('Статус'), max_length=50,
                              choices=(
                                  ('pending', _('В ожидании')),
                                  ('succeeded', _('Успешно')),
                                  ('canceled', _('Отменено')),
                                  ('failed', _('Ошибка')),
                                  ('refunded', _('Возврат')),
                                  ('captured', _('Захвачено')),  # Для платежей с предоплатой
                              ),
                              default='pending',
                              )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, )

    def __str__(self):
        return f"Платеж на {self.amount}p. {self.created_at.strftime('%Y-%m-%d %H:%M')} {str(self.status)} {str(self.user)} {str(self.paid)}"

    class Meta:
        verbose_name = 'Yookassa Payment'
        verbose_name_plural = 'Yookassa Payments'
