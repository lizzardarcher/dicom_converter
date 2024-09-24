from django.urls import path
from apps.payments import views

urlpatterns = [
    path('yookassa/process_payment/', views.ProcessPaymentYookassaView.as_view(), name='yookassa_process_payment'),
    path('yookassa/success/', views.SuccessYookassaView.as_view(), name='yookassa_success'),
    path('yookassa/cancel/', views.CancelYookassaView.as_view(), name='yookassa_cancel'),
    path('yookassa/webhook/', views.WebhookYookassaView.as_view(), name='yookassa_webhook'),
]