import logging
import sys
import traceback
from datetime import datetime, timezone, timedelta
from time import sleep

import yadisk
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'dicom_converter.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from django.conf import settings
from apps.converter.models import Research
from apps.converter.utils import CustomFormatter, send_email_with_attachment

### LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


def delete_old_research():
    # Получаем дату, которая была 3 дня назад
    threshold_date = datetime.now() - timedelta(days=3)

    # Удаляем объекты, созданные до целевой даты
    objects = Research.objects.filter(date_created__lt=threshold_date)

    for obj in objects:
        os.remove(f'/opt/dicom_converter/static/media/{obj.ready_archive.name}')


def upload(file_path, email, research_id):
    client = yadisk.Client(token=settings.YANDEX_TOKEN)
    with client:
        try:
            _dir = f'research_{datetime.now().strftime("%Y-%m-%d %H:%M")}'

            logger.info(f"9.1. [upload_file_path] [{file_path}]")
            client.upload(file_path, f"disk:/{_dir}", overwrite=True, timeout=3600)

            # logger.info(f"9.2. [publish] [app:/Test/{file}]")
            client.publish(f'disk:/{_dir}')

            m = client.get_meta(f'disk:/{_dir}').file

            send_email_with_attachment(
                to_email=email,
                subject='Тестовое письмо без вложения',
                body=f'Привет! Это тестовое письмо без вложения.\n'
                     f'Ссылка на исследование\n'
                     f'{m}',
            )
            Research.objects.filter(id=int(research_id)).update(cloud_url=m, is_cloud_upload=True)

        except Exception as e:
            logger.fatal(traceback.format_exc())


if __name__ == '__main__':
    try:
        while True:

            # Отправка в облако и создание публичных ссылок на исследования
            res_list = Research.objects.filter(is_cloud_upload=False)
            if res_list:
                for res in res_list:
                    logger.info(f'[NEW ARCHIVE TO UPLOAD] [{res.ready_archive}] [{res.date_created}]')
                    start_time = datetime.now()
                    upload(file_path=f'/opt/dicom_converter/static/media/{res.ready_archive.name}',
                           email=res.user.email,
                           research_id=res.id)
                    end_time = datetime.now()
                    logger.info(f'[UPLOAD SUCCESS] [FINISHED TIME] [{end_time - start_time}]')
                sleep(5)
            else:
                logger.info(f'[--EMPTY RESEARCH LIST--]')
                sleep(5)
            try:
                #  Очищение места на сервере / удаление старых архивов
                delete_old_research()
            except Exception as e:
                logger.fatal(traceback.format_exc())

    except KeyboardInterrupt:
        sys.exit(0)
