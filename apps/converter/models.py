import os
import shutil
import traceback

import patoolib
from datetime import datetime
from pathlib import Path

from django.db import models
from django.core.files import File
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

from apps.home.models import Log
from dicom_converter.logger.project_logger import logger
from dicom_converter.settings import BASE_DIR, MEDIA_ROOT
from apps.converter.utils import find_dir_by_name_part, search_file_in_dir, add_ext_recursive, unidecode_recursive, \
    copy_files, find_folder, find_directory, delete_file_recursively
from apps.converter import galileos_converter



class Research(models.Model):
    user = models.ForeignKey(User, related_name='converters', blank=True, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    raw_archive = models.FileField(upload_to="converter/raw/", null=False, blank=False,
                                   validators=[FileExtensionValidator(['rar', 'zip', '7z'])],
                                   verbose_name='Архив от пользователя')
    is_anonymous = models.BooleanField(null=True, default=True, verbose_name='Анонимизировать данные')
    is_one_file = models.BooleanField(null=True, default=True, verbose_name='Одним файлом')
    is_cloud_upload = models.BooleanField(null=True, default=False, verbose_name='Отправлен в облако')
    ready_archive = models.FileField(upload_to="converter/ready", null=True, blank=True,
                                     verbose_name="Архив с готовыми данными")
    cloud_url = models.URLField(max_length=1000, null=True, blank=True, verbose_name='Ссылка на архив')
    status = models.BooleanField(default=True, null=True, blank=True, verbose_name='Статус исследования')
    error_message = models.TextField(max_length=5000, null=True, blank=True, verbose_name='Сообщение об ошибке')
    slug = models.SlugField(unique=True, max_length=200, blank=True)

    def __str__(self):
        return str(self.raw_archive).split('/')[-1]

    def save(self, *args, **kwargs):
        start_time = datetime.now()
        if not self.slug:
            self.slug = slugify(f'{self.user}{str(datetime.now())}')
        self.raw_archive.name = self.raw_archive.name.replace(' ', '')
        super(Research, self).save(*args, **kwargs)
        try:
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
                elif'.7z' in self.raw_archive.name:
                    patoolib.extract_archive(archive=archive_dir, outdir=output_dir, program='/usr/bin/7z')
                else:
                    patoolib.extract_archive(archive=archive_dir, outdir=output_dir)

                # 2.1 Ищем название файла с исследованием
                target_dir_name = 'vol_0'
                unidecode_recursive(MEDIA_ROOT.joinpath('converter').joinpath('extract_dir').__str__())
                glx_src_dir = Path(find_dir_by_name_part(start_path=output_dir, target_dir_name=target_dir_name))
                logger.info(f'4. [Директория откуда работает gxl2dicom] {glx_src_dir}')

                glx_dstr_dir = Path(glx_src_dir).parent.joinpath('ready')
                logger.info(f'5. [Директория куда gxl2dicom отправляет готовые файлы] {glx_dstr_dir}')

                # 3. Прогоняем архив через galileos_converter.py
                galileos_converter.glx2dicom(srcdir=Path(f'{glx_src_dir}'), dstdir=Path(f'{glx_dstr_dir}'))

                # 4. Прогоняем полученные файлы через renamer.py
                add_ext_recursive(glx_dstr_dir.__str__(), '.dcm')

                # 5. Архивируем полученное исследование
                ready_archive = f"{self.date_created.now().strftime('%Y_%m_%d_%H_%M_')}{self.raw_archive.name.replace('converter/raw/', '')}"
                logger.info(f"6. {ready_archive}")
                logger.info(f"7. {glx_dstr_dir.__str__()}")

                # Если одним фалом, то ...
                if self.is_one_file:
                    one_file = galileos_converter.merge_dicom(
                        input_dir=f'{glx_dstr_dir.__str__()}',
                        output_filename=f'{self.date_created.now().strftime('%Y_%m_%d_%H_%M_')}_research.dcm')

                    patoolib.create_archive(
                        archive=ready_archive,
                        filenames=(one_file,))
                else:
                    try:
                        cur_path = f'/{datetime.now().strftime("%Y%m%d%H%M%S")}'
                        logger.info(f'[CURRENT PATH] [{cur_path}]')

                        move = shutil.move(glx_dstr_dir.__str__(), cur_path)
                        delete_file_recursively(cur_path, 'DICOMDIR.dcm')
                        logger.info(f'[MOVED SUCCESS] [{move}]')
                        patoolib.create_archive(
                            archive=ready_archive,
                            filenames=(cur_path,),
                        )
                        try:
                            shutil.rmtree(cur_path)
                            logger.info(f'[DELETED SUCCESS] [{cur_path}]')
                        except OSError as e:
                            logger.fatal("Error: %s - %s." % (e.filename, e.strerror))

                    except:
                        logger.error(traceback.format_exc())
                        patoolib.create_archive(
                            archive=ready_archive,
                            filenames=(glx_dstr_dir.__str__(),),
                        )

                file = search_file_in_dir(BASE_DIR, ready_archive)
                logger.info(f"8. {file}")
                os.replace(file, str(MEDIA_ROOT.joinpath("converter/ready") / file.split('/')[-1]))

                # 6. Сохраняем ссылку на архив в модель
                Research.objects.filter(id=self.id).update( ready_archive=File(file, name=f"converter/ready/{file.split('/')[-1]}"))
                UserSettings.objects.filter(user=self.user).update(research_avail_count=(avail - 1))

                try:
                    os.remove(archive_dir)
                    shutil.rmtree(output_dir)
                except OSError as e:
                    logger.fatal("Error: %s - %s." % (e.filename, e.strerror))

                file_path = ('/opt/dicom_converter/static/media/' + Research.objects.filter(id=self.id).last().ready_archive.name)

                logger.info(f"9. [file_path attached to email] {file_path}")
                logger.info(f'10. [SUCCESS] [PROCESS FINESHED IN] [{datetime.now() - start_time}]')
                Log.objects.create(user=self.user, level='info', message='[CONVERTATION] [SUCCESS]')
        except OSError:
            Research.objects.filter(id=self.id).update(error_message=f'{traceback.format_exc()}')
            Log.objects.create(user=self.user, level='error', message=f'[CONVERTATION] [FAIL] {traceback.format_exc()}')
        except Exception as e:
            Research.objects.filter(id=self.id).update(error_message=f'{traceback.format_exc()}')
            Log.objects.create(user=self.user, level='error', message=f'{traceback.format_exc()}')


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


class GlobalSettings(models.Model):
    price_1_ru = models.IntegerField(default=200, blank=True, null=True, verbose_name='Цена за 1 конв. РУБ')
    price_2_ru = models.IntegerField(default=900, blank=True, null=True, verbose_name='Цена за 5 конв. РУБ')
    price_3_ru = models.IntegerField(default=1700, blank=True, null=True, verbose_name='Цена за 10 конв. РУБ')

    price_1_en = models.IntegerField(default=2, blank=True, null=True, verbose_name='Цена за 1 конв. USD')
    price_2_en = models.IntegerField(default=9, blank=True, null=True, verbose_name='Цена за 5 конв. USD')
    price_3_en = models.IntegerField(default=17, blank=True, null=True, verbose_name='Цена за 10 конв. USD')

    def __str__(self):
        return "Настройка цен"

    class Meta:
        verbose_name = 'Цены'
        verbose_name_plural = 'Цены'


class TestResearch(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    raw_archive = models.FileField(null=False, blank=False, verbose_name='Архив от пользователя')

    def __str__(self):
        return str(self.raw_archive).split('/')[-1]
