import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from time import sleep

import patoolib
from django.core.files import File
from django.template import context
from django.utils.text import slugify
from unidecode import unidecode

from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render
from django.views.generic import CreateView, ListView

from apps.converter.forms import ResearchUploadForm
from apps.converter.models import Research, UserSettings
from apps.converter.utils import CustomFormatter, unidecode_recursive, find_dir_by_name_part, add_ext_recursive, \
    search_file_in_dir
from dicom_converter.settings import MEDIA_ROOT, BASE_DIR

### LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


class UploadResearchView(SuccessMessageMixin, CreateView):
    model = Research
    form_class = ResearchUploadForm
    success_url = '/'
    template_name = 'pages/upload_research.html'

    def get_context_data(self, **kwargs):
        context = super(UploadResearchView, self).get_context_data(**kwargs)
        context.update({
            'research': Research.objects.filter(user=self.request.user),
        })
        return context

    def get_success_url(self):
        return '/upload_research'

    def get_success_message(self, cleaned_data):
        return f"Архив успешно обработан {cleaned_data['raw_archive'].name}"

    def form_valid(self, form):
        form.instance.user = self.request.user
        #  Переименовываем название raw_archive в латиницу
        name = form.cleaned_data['raw_archive'].name
        date_created = form.cleaned_data['date_created']
        dots = int(str(name).count('.'))
        name = unidecode(str(name).strip().lower().replace(' ', '_', dots - 1))
        form.instance.raw_archive.name = name

        avail = UserSettings.objects.filter(user=self.request.user).last().research_avail_count
        if avail:
            start_time = datetime.now()
            """
                1. Получаем архив с исследованием с сайта (OK)

                2. Разархивируем полученный архив (OK)
                Используем стороннюю библиотеку patoolib. Архив берется по пути, указанному в модели далее извлекается в
                динамически создающуюся директорию, соответствующую имени архива без расширения

            """
            archive_dir = f"{str(MEDIA_ROOT)}/{name}"
            logger.info(f'2. [Директория с архивом] {archive_dir}')

            output_dir = f"{str(MEDIA_ROOT)}/converter/extract_dir/{str(name).split('.')[0].replace('converter/raw/', '')}/"
            logger.info(f'3. [Директория разархивирования] {output_dir}')

            if '.rar' in name:
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

            os.system(f"python {BASE_DIR.joinpath('apps/converter/glx.py')} {glx_src_dir} {glx_dstr_dir}")
            sleep(7)

            # 4. Прогоняем полученные файлы через renamer.py

            add_ext_recursive(glx_dstr_dir.__str__(), '.dcm')

            # 5. Архивируем полученное исследование
            ready_archive = f"{date_created.now().strftime('%Y_%m_%d_%H_%M_')}{name.replace('converter/raw/', '')}"
            logger.info(f"6. {ready_archive}")
            logger.info(f"7. {glx_dstr_dir.__str__()}")

            if '.rar' in name:
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
            end_time = datetime.now()

            try:
                os.remove(archive_dir)
                shutil.rmtree(output_dir)
            except OSError as e:
                logger.fatal("Error: %s - %s." % (e.filename, e.strerror))

            logger.info(f'9. [SUCCESS] [PROCESS FINESHED IN] [{end_time - start_time}]')
        return super().form_valid(form)
