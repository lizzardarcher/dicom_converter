import os
import shutil
import patoolib
from datetime import datetime
from pathlib import Path

from django.db import models
from django.core.files import File
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

from dicom_converter.logger.project_logger import logger
from dicom_converter.settings import BASE_DIR, MEDIA_ROOT
from apps.converter.utils import find_dir_by_name_part, search_file_in_dir,  add_ext_recursive, unidecode_recursive
from apps.converter import glx


class Research(models.Model):
    user = models.ForeignKey(User, related_name='converters', blank=True, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    raw_archive = models.FileField(upload_to="converter/raw/", null=False, blank=False,
                                   validators=[FileExtensionValidator(['rar', 'zip'])],
                                   verbose_name='Архив от пользователя')
    is_anonymous = models.BooleanField(null=True, default=True, verbose_name='Анонимизировать данные')
    is_one_file = models.BooleanField(null=True, default=True, verbose_name='Одним файлом')
    is_cloud_upload = models.BooleanField(null=True, default=False, verbose_name='Отправлен в облако')
    ready_archive = models.FileField(upload_to="converter/ready", null=True, blank=True,
                                     verbose_name="Архив с готовыми данными")
    cloud_url = models.URLField(max_length=1000, null=True, blank=True, verbose_name='Ссылка на архив')
    status = models.BooleanField(default=True, null=True, blank=True, verbose_name='Статус исследования')
    slug = models.SlugField(unique=True, max_length=200, blank=True)

    def __str__(self):
        return str(self.raw_archive).split('/')[-1]

    def save(self, *args, **kwargs):
        start_time = datetime.now()
        if not self.slug:
            self.slug = slugify(f'{self.user}{str(datetime.now())}')
        self.raw_archive.name = self.raw_archive.name.replace(' ', '')
        super(Research, self).save(*args, **kwargs)
        avail = UserSettings.objects.filter(user=self.user).last().research_avail_count
        if avail:
            """
                1. Получаем архив с исследованием с сайта (OK)

                2. Разархивируем полученный архив (OK)
                Используем стороннюю библиотеку patoolib. Архив берется по пути, указанному в модели далее извлекается в
                динамически создающуюся директорию, соответствующую имени архива без расширения
            """
            archive_dir = f"{str(MEDIA_ROOT)}/{self.raw_archive.name}"
            logger.info(f'2. [Директория с архивом] {archive_dir}')

            output_dir = f"{str(MEDIA_ROOT)}/converter/extract_dir/{str(self.raw_archive.name).split('.')[0].replace('converter/raw/', '')}/"
            logger.info(f'3. [Директория разархивирования] {output_dir}')

            if '.rar' in self.raw_archive.name:
                patoolib.extract_archive(archive=archive_dir, outdir=output_dir, program='/usr/bin/rar')
            else:
                patoolib.extract_archive(archive=archive_dir, outdir=output_dir)

            # 2.1 Ищем название файла с исследованием
            target_dir_name = 'vol_0'
            unidecode_recursive(MEDIA_ROOT.joinpath('converter').joinpath('extract_dir').__str__())
            glx_src_dir = Path(find_dir_by_name_part(start_path=output_dir, target_dir_name=target_dir_name))
            logger.info(f'4. [Директория откуда работает gxl2dicom] {glx_src_dir}')

            glx_dstr_dir = Path(glx_src_dir).parent.joinpath('ready')
            logger.info(f'5. [Директория куда gxl2dicom отправляет готовые файлы] {glx_dstr_dir}')

            # 3. Прогоняем архив через glx.py
            glx.glx2dicom(srcdir=Path(f'{glx_src_dir}'), dstdir=Path(f'{glx_dstr_dir}'))

            # 4. Прогоняем полученные файлы через renamer.py
            add_ext_recursive(glx_dstr_dir.__str__(), '.dcm')

            # 5. Архивируем полученное исследование
            ready_archive = f"{self.date_created.now().strftime('%Y_%m_%d_%H_%M_')}{self.raw_archive.name.replace('converter/raw/', '')}"
            logger.info(f"6. {ready_archive}")
            logger.info(f"7. {glx_dstr_dir.__str__()}")

            # Если одним фалом, то ...
            if self.is_one_file:
                one_file = glx.merge_dicom(
                    input_dir=f'{glx_dstr_dir.__str__()}',
                    output_filename=f'{self.date_created.now().strftime('%Y_%m_%d_%H_%M_')}_research.dcm')

                if '.rar' in self.raw_archive.name:
                    patoolib.create_archive(
                        archive=ready_archive,
                        filenames=(one_file,), program='/usr/bin/rar')
                else:
                    patoolib.create_archive(
                        archive=ready_archive,
                        filenames=(one_file,))
            else:
                if '.rar' in self.raw_archive.name:
                    patoolib.create_archive(
                        archive=ready_archive,
                        filenames=(glx_dstr_dir.__str__(),), program='/usr/bin/rar')
                else:
                    patoolib.create_archive(
                        archive=ready_archive,
                        filenames=(glx_dstr_dir.__str__(),))

            file = search_file_in_dir(BASE_DIR, ready_archive)
            logger.info(f"8. {file}")
            os.replace(file, str(MEDIA_ROOT.joinpath("converter/ready") / file.split('/')[-1]))

            # 6. Сохраняем ссылку на архив в модель
            Research.objects.filter(id=self.id).update(
                ready_archive=File(file, name=f"converter/ready/{file.split('/')[-1]}"))

            try:
                os.remove(archive_dir)
                shutil.rmtree(output_dir)
            except OSError as e:
                logger.fatal("Error: %s - %s." % (e.filename, e.strerror))

            UserSettings.objects.filter(user=self.user).update(research_avail_count=(avail - 1))

            file_path = ('/opt/dicom_converter/static/media/' +
                         Research.objects.filter(id=self.id).last().ready_archive.name)

            logger.info(f"9. [file_path attached to email] {file_path}")
            logger.info(f'10. [SUCCESS] [PROCESS FINESHED IN] [{datetime.now() - start_time}]')

    class Meta:
        verbose_name = 'Исследование'
        verbose_name_plural = 'Исследования'


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    research_avail_count = models.PositiveIntegerField(default=0, blank=True, null=True,
                                                       verbose_name='Количество доступных конвертаций')

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

    # price_1_ru = models.IntegerField(default=200, blank=True, null=True, verbose_name='Цена за 1 конв. РУБ')
    # price_2_ru = models.IntegerField(default=900, blank=True, null=True, verbose_name='Цена за 5 конв. РУБ')
    # price_3_ru = models.IntegerField(default=1700, blank=True, null=True, verbose_name='Цена за 10 конв. РУБ')
    #
    # price_1_en = models.IntegerField(default=2, blank=True, null=True, verbose_name='Цена за 1 конв. USD')
    # price_2_en = models.IntegerField(default=9, blank=True, null=True, verbose_name='Цена за 5 конв. USD')
    # price_3_en = models.IntegerField(default=17, blank=True, null=True, verbose_name='Цена за 10 конв. USD')

    class Meta:
        verbose_name = 'Общие Настройки проекта'
        verbose_name_plural = 'Общие Настройки проекта'


class TestResearch(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    raw_archive = models.FileField(null=False, blank=False, verbose_name='Архив от пользователя')

    def __str__(self):
        return str(self.raw_archive).split('/')[-1]

