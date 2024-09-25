import json
import logging
import sys
import uuid
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from yookassa import Payment as YooKassaPayment, Configuration

from apps.converter.models import UserSettings
from apps.payments.models import Payment
from apps.payments.forms import PaymentForm


class SelectPaymentView(TemplateView):
    template_name = 'payments/select.html'

class PaymentInfoYookassaView(TemplateView, LoginRequiredMixin):
    template_name = 'payments/yookassa/payment_info.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'payment_info': 'e'
        })
        try:
            Configuration.account_id = int(settings.YOOKASSA_SHOP_ID)
            Configuration.secret_key = settings.YOOKASSA_SECRET
            user = User.objects.get(pk=self.request.GET['user'])
            payment = Payment.objects.filter(user=user).last()
            yookassa_payment = YooKassaPayment.find_one(payment.payment_id)
            context.update({
                'payment_info': yookassa_payment
            })
        except Exception as e:
            context.update({
                'payment_info': e
            })

        return context


class ProcessPaymentYookassaView(FormView, LoginRequiredMixin):
    template_name = 'payments/yookassa/process_payment.html'
    form_class = PaymentForm
    success_url = reverse_lazy('yookassa_success')  # URL успешной оплаты

    def form_valid(self, form):
        description = form.cleaned_data['description']
        amount = 200
        if description == '1_convert':
            amount = 200
        elif description == '5_convert':
            amount = 900
        elif description == '10_convert':
            amount = 1700
        payment = Payment.objects.create(
            amount=amount,
            description=description,
            user=self.request.user,
            currency='RUB'
        )

        Configuration.account_id = int(settings.YOOKASSA_SHOP_ID)
        Configuration.secret_key = settings.YOOKASSA_SECRET

        payment_object = YooKassaPayment.create({
            'amount': {
                'value': amount,
                'currency': 'RUB',
            },
            'confirmation': {
                'type': 'redirect',
                'return_url': f'https://galileos.pro/payments/yookassa/payment_info?user={self.request.user.pk}',
            },
            'capture': True,
            'description': description,
        }, uuid.uuid4())

        payment.payment_id = payment_object.id
        payment.save()
        return redirect(payment_object.confirmation.confirmation_url)


