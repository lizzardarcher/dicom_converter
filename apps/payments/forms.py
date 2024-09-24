from django import forms
from django.utils.translation import gettext_lazy as _


class PaymentForm(forms.Form):
    CHOICES = (('1_convert', _('Оплатить 1 конвертацию')),
               ('5_convert', _('Оплатить 5 конвертаций')),
               ('10_convert', _('Оплатить 10 конвертаций')),               )
    description = forms.ChoiceField(choices=CHOICES)
