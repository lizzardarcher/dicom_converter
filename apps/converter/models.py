import os
from datetime import datetime
from time import sleep

import patoolib

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from pathlib import Path

from apps.converter.utils import find_dir_by_name_part, add_dcm_extension, rename_files_recursive
from dicom_converter.settings import BASE_DIR
from apps.converter import glx


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
        return str(self.user) + ' ' + str(self.date_created)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.user}{str(datetime.now())}')
        super(Research, self).save(*args, **kwargs)

        """
            1. Получаем архив с исследованием с сайта (OK)
            
            2. Разархивируем полученный архив (OK)
            Используем стороннюю библиотеку patoolib. Архив берется по пути, указанному в модели далее извлекается в
            динамически создающуюся директорию, соответствующую имени архива без расширения
            
        """

        archive_dir = f"{str(BASE_DIR)}/{self.raw_archive.name}"
        print('archive_dir:',archive_dir)

        output_dir = f"{str(BASE_DIR)}/converter/extract_dir/{str(self.raw_archive.name).split('.')[0].replace('converter/raw/', '')}/"
        print('output_dir:', output_dir)

        patoolib.extract_archive(archive=archive_dir, outdir=output_dir)

        # 2.1 Ищем название файла с исследованием
        target_dir_name = 'vol_0'
        glx_src_dir = Path(find_dir_by_name_part(start_path=output_dir, target_dir_name=target_dir_name))
        print('glx_src_dir:', glx_src_dir)
        glx_dstr_dir= Path(glx_src_dir).parent.joinpath('ready')
        print('glx_dstr_dir: ',glx_dstr_dir)
        # 3. Прогоняем архив через glx.py

        os.system(f"python {BASE_DIR.joinpath('apps/converter/glx.py')} {glx_src_dir} {glx_dstr_dir}")

        # glx.glx2dicom(srcdir=glx_src_dir, dstdir=glx_dstr_dir, dicom_attrs={})

        # 4. Прогоняем полученные файлы через renamer.py

        rename_files_recursive(glx_dstr_dir.__str__(), '.dcm')

        # 5. Архивируем полученное исследование

        # patoolib.create_archive()

        # 6. Сохраняем ссылку на архив в модель

        Research.objects.filter(id=self.id).update(ready_archive="SOME_READY_ARCHIVE")

    class Meta:
        verbose_name = 'Исследование'
        verbose_name_plural = 'Исследования'
