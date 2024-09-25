from django.urls import path
from apps.payments import views

urlpatterns = [
    path('select/', views.SelectPaymentView.as_view(), name='select_payment'),

    path('yookassa/process_payment/', views.ProcessPaymentYookassaView.as_view(), name='yookassa_process_payment'),
    path('yookassa/payment_info/', views.PaymentInfoYookassaView.as_view(), name='payment_info'),
]