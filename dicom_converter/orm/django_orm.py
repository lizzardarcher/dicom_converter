import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'dicom_converter.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()