from django.contrib.auth.models import User
from django.db import models
from django.utils.html import html_safe
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    """Модель платежа."""

    amount = models.DecimalField(_('Сумма'), max_digits=10, decimal_places=2, blank=True)
    description = models.CharField(_('Описание'), max_length=255,
                                   choices=(
                                       ('1_convert', _('Оплатить 1 конвертацию')),
                                       ('5_convert', _('Оплатить 5 конвертаций')),
                                       ('10_convert', _('Оплатить 10 конвертаций')),
                                   ), blank=False)
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
                                  ('captured', _('Захвачено')),
                              ),
                              default='pending',
                              )
    currency = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, )

    def __str__(self):
        if self.status == 'pending':
            status = f"<span class='badge badge-warning'>{self.status}</span>"
        elif self.status == 'succeeded':
            status = f"<span class='badge badge-success'>{self.status}</span>"
        elif self.status == 'canceled' or self.status == 'failed':
            status = f"<span class='badge badge-danger'>{self.status}</span>"
        else:
            status = f"<span class='badge badge-secondary'>{self.status}</span>"

        if self.paid:
            paid = '✅'
        else:
            paid = '❌'
        return mark_safe(f"Платеж на <span class='badge badge-info'>{self.amount}</span>p. {self.created_at.strftime('%Y-%m-%d %H:%M')} {status} {str(self.user)} {paid}")

    class Meta:
        verbose_name = 'Yookassa Payment'
        verbose_name_plural = 'Yookassa Payments'
