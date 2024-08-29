import logging
import os
import shutil
import sys
from datetime import datetime
from time import sleep
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.termcolors import color_names
from django.utils.text import slugify
from unidecode import unidecode
import patoolib



from apps.converter.utils import find_dir_by_name_part, search_file_in_dir, CustomFormatter, add_ext_recursive, \
    unidecode_recursive
from dicom_converter.settings import BASE_DIR, MEDIA_ROOT
from apps.converter import glx

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

    def delete(self, *args, **kwargs):
        # try:
        #     os.remove(f"{str(MEDIA_ROOT)}/{self.raw_archive.name}")
        #     print(f"{str(MEDIA_ROOT)}/{self.raw_archive.name}")
        # except OSError as e:
        #     logger.fatal("Error: %s - %s." % (e.filename, e.strerror))
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        start_time = datetime.now()
        if not self.slug:
            self.slug = slugify(f'{self.user}{str(datetime.now())}')
        self.raw_archive.name = self.raw_archive.name.replace(' ','')
        super(Research, self).save(*args, **kwargs)
        """
            1. Получаем архив с исследованием с сайта (OK)
            
            2. Разархивируем полученный архив (OK)
            Используем стороннюю библиотеку patoolib. Архив берется по пути, указанному в модели далее извлекается в
            динамически создающуюся директорию, соответствующую имени архива без расширения
            
        """
        logger.info(f"1. [MEDIA_ROOT] [{MEDIA_ROOT}]")
        print('****', MEDIA_ROOT.joinpath('converter').joinpath('extract_dir'))

        archive_dir = f"{str(MEDIA_ROOT)}/{self.raw_archive.name}"
        logger.info(f'2. [Директория с архивом] {archive_dir}')

        output_dir = f"{str(MEDIA_ROOT)}/converter/extract_dir/{str(self.raw_archive.name).split('.')[0].replace('converter/raw/', '')}/"
        # ur = unidecode_recursive(output_dir)
        # print(ur)
        logger.info(f'3. [Директория разархивирования] {output_dir}')

        if '.rar' in self.raw_archive.name:
            patoolib.extract_archive(archive=archive_dir, outdir=output_dir, program='/usr/bin/rar')
        else:
            patoolib.extract_archive(archive=archive_dir, outdir=output_dir)
        # 2.1 Ищем название файла с исследованием

        target_dir_name = 'vol_0'
        # glx_src_dir = Path(find_dir_by_name_part(start_path=output_dir, target_dir_name=target_dir_name))
        unidecode_recursive(MEDIA_ROOT.joinpath('converter').joinpath('extract_dir').__str__())
        glx_src_dir = Path(find_dir_by_name_part(start_path=output_dir, target_dir_name=target_dir_name))
        logger.info(f'4. [Директория откуда работает gxl2dicom] {glx_src_dir}')

        glx_dstr_dir = Path(glx_src_dir).parent.joinpath('ready')
        # os.rename(glx_dstr_dir.__str__(), unidecode(glx_src_dir.__str__()))
        logger.info(f'5. [Директория куда gxl2dicom отправляет готовые файлы] {glx_dstr_dir}')

        # 3. Прогоняем архив через glx.py

        os.system(f"python {BASE_DIR.joinpath('apps/converter/glx.py')} {glx_src_dir} {glx_dstr_dir}")
        sleep(7)
        # glx.glx2dicom(srcdir=glx_src_dir, dstdir=glx_dstr_dir, dicom_attrs={})

        # 4. Прогоняем полученные файлы через renamer.py

        add_ext_recursive(glx_dstr_dir.__str__(), '.dcm')

        # 5. Архивируем полученное исследование
        ready_archive = f"{self.date_created.now().strftime('%Y_%m_%d_%H_%M_')}{self.raw_archive.name.replace('converter/raw/', '')}"
        logger.info(f"6. {ready_archive}")
        logger.info(f"7. {glx_dstr_dir.__str__()}")

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
        os.replace(file, str(MEDIA_ROOT.joinpath("converter/ready")/file.split('/')[-1]))
        # 6. Сохраняем ссылку на архив в модель

        Research.objects.filter(id=self.id).update(ready_archive=File(file, name=f"converter/ready/{file.split('/')[-1]}"))
        end_time = datetime.now()

        try:
            os.remove(archive_dir)
            shutil.rmtree(output_dir)
        except OSError as e:
            logger.fatal("Error: %s - %s." % (e.filename, e.strerror))

        logger.info(f'9. [SUCCESS] [PROCESS FINESHED IN] [{end_time - start_time}]')

    class Meta:
        verbose_name = 'Исследование'
        verbose_name_plural = 'Исследования'

