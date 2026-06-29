import uuid

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.urls import reverse, reverse_lazy

from yookassa import Payment as YooKassaPayment, Configuration

from apps.converter.models import UserSettings, GlobalSettings
from apps.home.models import Log
from apps.payments.models import Payment
from apps.payments.forms import PaymentForm


class SelectPaymentView(TemplateView):
    template_name = 'payments/select.html'


class PaymentInfoYookassaView(TemplateView, LoginRequiredMixin):
    template_name = 'payments/yookassa/payment_info.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_info'] = None
        context['payment_error'] = None
        try:
            Configuration.account_id = int(settings.YOOKASSA_SHOP_ID)
            Configuration.secret_key = settings.YOOKASSA_SECRET
            payment = Payment.objects.filter(user=self.request.user).last()
            if not payment or not payment.payment_id:
                context['payment_error'] = 'Платёж не найден.'
                return context
            context['payment_info'] = YooKassaPayment.find_one(payment.payment_id)
        except Exception:
            context['payment_error'] = 'Не удалось загрузить информацию о платеже.'
        return context


class ProcessPaymentYookassaView(FormView, LoginRequiredMixin):
    template_name = 'payments/yookassa/process_payment.html'
    form_class = PaymentForm
    success_url = reverse_lazy('yookassa_success')  # URL успешной оплаты

    def form_valid(self, form):
        description = form.cleaned_data['description']
        prices = GlobalSettings.objects.get(pk=1)
        price = 200
        if description == '1_convert':
            price = prices.price_1_ru
        elif description == '5_convert':
            price = prices.price_2_ru
        elif description == '10_convert':
            price = prices.price_3_ru
        payment = Payment.objects.create(
            amount=price,
            description=description,
            user=self.request.user,
            currency='RUB'
        )

        Configuration.account_id = int(settings.YOOKASSA_SHOP_ID)
        Configuration.secret_key = settings.YOOKASSA_SECRET

        payment_object = YooKassaPayment.create({
            'amount': {
                'value': price,
                'currency': 'RUB',
            },
            'confirmation': {
                'type': 'redirect',
                'return_url': self.request.build_absolute_uri(reverse('payment_info')),
            },
            'capture': True,
            'description': description,
        }, uuid.uuid4())

        payment.payment_id = payment_object.id
        payment.save()
        Log.objects.create(user=self.request.user, level='info', message=f'[{str(payment_object.id)}] [Payment] [{description}]')
        return redirect(payment_object.confirmation.confirmation_url)
