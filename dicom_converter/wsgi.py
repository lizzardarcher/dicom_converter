"""from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
WSGI config for dicom_converter project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dicom_converter.settings')

application = get_wsgi_application()
