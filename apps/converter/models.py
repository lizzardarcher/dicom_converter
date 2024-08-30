import os
import shutil
import logging
from datetime import datetime
from time import sleep
from pathlib import Path

from django.db import models
from django.core.files import File
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import patoolib

from dicom_converter.settings import BASE_DIR, MEDIA_ROOT
from apps.converter.utils import find_dir_by_name_part, search_file_in_dir, CustomFormatter, add_ext_recursive, unidecode_recursive

### LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


class Research(models.Model):
    user = models.ForeignKey(User, related_name='converters', blank=True, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    raw_archive = models.FileField(upload_to="converter/raw/", null=False, blank=False,
                                   validators=[FileExtensionValidator(['rar', 'zip'])],
                                   verbose_name='Архив от пользователя')
    is_anonymous = models.BooleanField(null=True, default=True, verbose_name='Анонимизировать данные')
    ready_archive = models.FileField(upload_to="converter/ready", null=True, blank=True,
                                     verbose_name="Архив с готовыми данными")
    slug = models.SlugField(unique=True, max_length=200, blank=True)

    def __str__(self):
        return str(self.raw_archive).split('/')[-1]

    # def delete(self, *args, **kwargs):
    #     archive_dir = f"{str(MEDIA_ROOT)}/{self.raw_archive.name}"
    #     try:
    #         print(f"{str(MEDIA_ROOT)}/{self.raw_archive.name}")
    #         os.remove(archive_dir)
    #     except OSError as e:
    #         logger.fatal("Error: %s - %s." % (e.filename, e.strerror))
    #     super().delete(*args, **kwargs)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.user}{str(datetime.now())}')
        self.raw_archive.name = self.raw_archive.name.replace(' ', '')
        super(Research, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Исследование'
        verbose_name_plural = 'Исследования'


from django.contrib.auth.models import User
from django.db import models, Error


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    research_avail_count = models.IntegerField(default=0, blank=True, null=True, verbose_name='Количество доступных конвертаций')

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Информация о пользователе'
        verbose_name_plural = 'Информация о пользователе'


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Количество')
    currency = models.CharField(max_length=100, blank=True, null=True, verbose_name='Валюта')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')

    def __str__(self):
        return f"Транзакция пользователя - {self.user.username}: {self.amount} от {self.timestamp}"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'


class GlobalSettings(models.Model):
    yookassa_api_key = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Yookassa token')
    yookassa_shop_id = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Yookassa Shop ID')

    class Meta:
        verbose_name = 'Общие Настройки проекта'
        verbose_name_plural = 'Общие Настройки проекта'

