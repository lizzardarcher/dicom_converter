from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from apps.home import views

urlpatterns = [
    path('prices', views.PricesView.as_view(), name='prices'),
    path('create', views.HomeCreateView.as_view(), name='create'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)