"""
URL configuration for dicom_converter project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import apps.home.views as home_views

urlpatterns = i18n_patterns(
    path('', include('apps.converter.urls')),

    path('', include('apps.admin_soft.urls')),

    path('', include('apps.home.urls')),

    path("i18n/", include("django.conf.urls.i18n")),

    path('admin/', admin.site.urls),

    path("cookies/", include("cookie_consent.urls")),

    path('payments/', include('apps.payments.urls')),
)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
