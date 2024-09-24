from django import forms


class PaymentForm(forms.Form):
    amount = forms.DecimalField(label='Сумма', required=True)
    description = forms.CharField(label='Описание', required=True)