from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from apps.home import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('set_lang_en', views.set_lang_en, name='set_lang_en'),
    path('set_lang_ru', views.set_lang_ru, name='set_lang_ru'),

    path('prices', views.PricesView.as_view(), name='prices'),
    path('price_info', views.PriceInfoView.as_view(), name='price_info'),
    path('privacy', views.PrivacyView.as_view(), name='privacy'),
    path('help', views.HelpView.as_view(), name='help'),
    path('sitemap', views.SiteMapView.as_view(), name='sitemap'),
    path('detailed_info', views.DetailedInfoView.as_view(), name='detailed_info'),
    path('about', views.AboutView.as_view(), name='about'),
    path('oferta', views.OfertaView.as_view(), name='oferta'),
    path('faq', views.FAQView.as_view(), name='faq'),
    path('how_it_works', views.HowItWorksView.as_view(), name='how_it_works'),
    path('contacts', views.ContactView.as_view(), name='contacts'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
