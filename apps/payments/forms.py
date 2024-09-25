from django import forms
from django.utils.translation import gettext_lazy as _


class PaymentForm(forms.Form):
    CHOICES = (('1_convert', _('1 КОНВЕРТАЦИЯ')),
               ('5_convert', _('5 КОНВЕРТАЦИЙ')),
               ('10_convert', _('10 КОНВЕРТАЦИЙ')),               )
    description = forms.ChoiceField(choices=CHOICES)
