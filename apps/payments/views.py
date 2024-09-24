import json
import logging
import sys
import uuid
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from yookassa import Payment as YooKassaPayment, Configuration

from apps.payments.models import Payment
from apps.payments.forms import PaymentForm  # Предполагается, что у вас есть форма PaymentForm


class ProcessPaymentYookassaView(FormView, LoginRequiredMixin):
    template_name = 'payments/yookassa/process_payment.html'
    form_class = PaymentForm
    success_url = reverse_lazy('yookassa_success')  # URL успешной оплаты

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        description = form.cleaned_data['description']

        payment = Payment.objects.create(
            amount=amount,
            description=description,
            user=self.request.user,
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
                'return_url': 'https://galileos.pro/payments/yookassa/success',
            },
            'capture': True,
            'description': description,
        }, uuid.uuid4())

        payment.payment_id = payment_object.id
        payment.save()
        return redirect(payment_object.confirmation.confirmation_url)


class SuccessYookassaView(TemplateView, LoginRequiredMixin):
    template_name = 'payments/yookassa/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        Configuration.account_id = int(settings.YOOKASSA_SHOP_ID)
        Configuration.secret_key = settings.YOOKASSA_SECRET
        payments = Payment.objects.all()
        for payment in payments:
            try:
                yp = YooKassaPayment.find_one(payment.payment_id)
                payment.paid = yp.paid
                payment.status = yp.status
                payment.save()
            except:
                pass
        context['payment_id'] = self.request.GET.get('payment_id')
        return context



class CancelYookassaView(TemplateView, LoginRequiredMixin):
    template_name = 'payments/yookassa/cancel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_id'] = self.request.GET.get('payment_id')
        return context


class WebhookYookassaView(View):
    ### LOGGING

    @csrf_exempt
    def post(self, request):

        log_path = '/opt/dicom_converter/apps/payments/log'
        logger = logging.getLogger(__name__)
        logging.basicConfig(
            format='%(asctime)s %(levelname) -8s %(message)s',
            level=logging.DEBUG,
            datefmt='%Y.%m.%d %I:%M:%S',
            handlers=[
                # TimedRotatingFileHandler(filename=log_path, when='D', interval=1, backupCount=5),
                logging.StreamHandler(stream=sys.stderr)
            ],
        )

        event_data = json.loads(request.body.decode('utf-8'))
        logger.info(event_data)
        # Получение secret_key из настроек
        # secret_key = settings.YOO_KASSA_SECRET_KEY

        # Проверка подписи с использованием Client.verify_signature()
        # Проверка подписи с использованием Signature.check()
        # try:
        #     Signature.check(event_data, secret_key)
        # except SignatureVerificationError:
        #     return HttpResponse(status=400)

        # Обработка события
        event_type = event_data['event']

        if event_type == 'payment.succeeded':
            # Обработка успешного платежа
            payment_id = event_data['object']['id']
            try:
                payment = Payment.objects.get(payment_id=payment_id)
                payment.paid = True
                payment.status = 'succeeded'
                payment.save()
                # ...  дополнительные действия (например, отправка уведомления пользователю) ...

            except Payment.DoesNotExist:
                ...
        elif event_type == 'payment.canceled':
            ...

        return HttpResponse(status=200)
