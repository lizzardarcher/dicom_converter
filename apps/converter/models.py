import os
import shutil
import tempfile
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
from apps.converter.utils import (
    ConversionError,
    extract_archive_safe,
    find_galileos_vol_dir,
    add_ext_recursive,
    unidecode_recursive,
    delete_file_recursively,
)
from apps.converter import galileos_converter


def _get_tmp_dir() -> Path:
    tmp = MEDIA_ROOT / 'converter' / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


def _cleanup_path(path, *, is_dir=False):
    if not path:
        return
    try:
        if is_dir and os.path.isdir(path):
            shutil.rmtree(path)
        elif not is_dir and os.path.isfile(path):
            os.remove(path)
    except OSError as e:
        logger.critical("Cleanup error: %s - %s." % (getattr(e, 'filename', path), e.strerror))


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

        archive_dir = os.path.join(str(MEDIA_ROOT), self.raw_archive.name)
        output_dir = os.path.join(
            str(MEDIA_ROOT),
            'converter',
            'extract_dir',
            str(self.raw_archive.name).split('.')[0].replace('converter/raw/', ''),
        )

        staging_dir = None
        temp_dcm = None
        staging_archive = None

        try:
            user_settings = UserSettings.objects.filter(user=self.user).last()
            avail = user_settings.research_avail_count if user_settings else 0
            if not avail:
                logger.warning(f'[CONVERTATION] skipped: no quota for user {self.user}')
                return

            logger.info(f'2. [Директория с архивом] {archive_dir}')
            logger.info(f'3. [Директория разархивирования] {output_dir}')

            extract_archive_safe(archive_dir, output_dir)

            unidecode_recursive(str(MEDIA_ROOT / 'converter' / 'extract_dir'))
            glx_src_dir = Path(find_galileos_vol_dir(output_dir))
            logger.info(f'4. [Директория откуда работает gxl2dicom] {glx_src_dir}')

            glx_dstr_dir = Path(glx_src_dir).parent.joinpath('ready')
            logger.info(f'5. [Директория куда gxl2dicom отправляет готовые файлы] {glx_dstr_dir}')

            galileos_converter.glx2dicom(srcdir=Path(f'{glx_src_dir}'), dstdir=Path(f'{glx_dstr_dir}'))
            add_ext_recursive(glx_dstr_dir.__str__(), '.dcm')

            tmp_dir = _get_tmp_dir()
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_')
            ready_archive_name = f"{timestamp}{self.raw_archive.name.replace('converter/raw/', '')}"
            staging_archive = str(tmp_dir / ready_archive_name)
            logger.info(f"6. {ready_archive_name}")
            logger.info(f"7. {glx_dstr_dir.__str__()}")

            if self.is_one_file:
                temp_dcm = str(tmp_dir / f'{timestamp}_research.dcm')
                galileos_converter.merge_dicom(
                    input_dir=f'{glx_dstr_dir.__str__()}',
                    output_filename=temp_dcm,
                )
                patoolib.create_archive(archive=staging_archive, filenames=(temp_dcm,))
            else:
                staging_dir = tempfile.mkdtemp(dir=str(tmp_dir))
                logger.info(f'[STAGING PATH] [{staging_dir}]')
                shutil.move(glx_dstr_dir.__str__(), staging_dir)
                delete_file_recursively(staging_dir, 'DICOMDIR.dcm')
                try:
                    patoolib.create_archive(archive=staging_archive, filenames=(staging_dir,))
                except Exception:
                    logger.error(traceback.format_exc())
                    patoolib.create_archive(
                        archive=staging_archive,
                        filenames=(glx_dstr_dir.__str__(),),
                    )

            ready_dest = MEDIA_ROOT / 'converter' / 'ready' / os.path.basename(staging_archive)
            ready_dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging_archive, str(ready_dest))
            staging_archive = None

            with open(ready_dest, 'rb') as ready_file:
                Research.objects.filter(id=self.id).update(
                    ready_archive=File(ready_file, name=f'converter/ready/{ready_dest.name}')
                )
            UserSettings.objects.filter(user=self.user).update(research_avail_count=(avail - 1))

            file_path = os.path.join(str(MEDIA_ROOT), Research.objects.filter(id=self.id).last().ready_archive.name)
            logger.info(f"8. {ready_dest}")
            logger.info(f"9. [file_path attached to email] {file_path}")
            logger.info(f'10. [SUCCESS] [PROCESS FINESHED IN] [{datetime.now() - start_time}]')
            Log.objects.create(user=self.user, level='info', message='[CONVERTATION] [SUCCESS]')
        except ConversionError as e:
            error_message = str(e)
            logger.error(f'[CONVERTATION] [FAIL] {error_message}')
            Research.objects.filter(id=self.id).update(error_message=error_message, status=False)
            Log.objects.create(user=self.user, level='error', message=f'[CONVERTATION] [FAIL] {error_message}')
        except OSError:
            Research.objects.filter(id=self.id).update(error_message=f'{traceback.format_exc()}', status=False)
            Log.objects.create(user=self.user, level='error', message=f'[CONVERTATION] [FAIL] {traceback.format_exc()}')
        except Exception:
            Research.objects.filter(id=self.id).update(error_message=f'{traceback.format_exc()}', status=False)
            Log.objects.create(user=self.user, level='error', message=f'{traceback.format_exc()}')
        finally:
            _cleanup_path(archive_dir)
            _cleanup_path(output_dir, is_dir=True)
            if staging_dir:
                _cleanup_path(staging_dir, is_dir=True)
            if temp_dcm:
                _cleanup_path(temp_dcm)
            if staging_archive:
                _cleanup_path(staging_archive)

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
