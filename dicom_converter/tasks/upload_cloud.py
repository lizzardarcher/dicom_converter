from dicom_converter.orm import django_orm

import sys
from datetime import datetime
from time import sleep

import yadisk
from django.conf import settings

from apps.converter.models import Research
from apps.converter.utils import send_email_with_attachment
from dicom_converter.logger.project_logger import logger


def upload(file_path, email, research_id):
    client = yadisk.Client(token=settings.YANDEX_TOKEN)
    with client:
        try:
            logger.info(f"9.1. [upload_file_path] [{file_path}]")
            research = Research.objects.filter(id=int(research_id)).last()
            _dir = f'galileos_pro_research_{research.user.username}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
            client.upload(file_path, f"disk:/{_dir}", overwrite=True, timeout=3600)
            client.publish(f'disk:/{_dir}')
            link = client.get_meta(f'disk:/{_dir}').public_url

            logger.info(f'[LINK] [{link}]')

            send_email_with_attachment(
                to_email=email,
                subject='Galileos Pro Исследование готово',
                body=f'Готовое исследование доступно для скачивания.\n'
                     f'Файлы успешно сконвертированы в формат DICOM\n'
                     f'Ссылка на исследование:\n{link}',
            )
            Research.objects.filter(id=int(research_id)).update(cloud_url=link, is_cloud_upload=True)

        except Exception as e:
            # logger.fatal(traceback.format_exc())
            logger.fatal(e)


if __name__ == '__main__':
    try:
        while True:

            # Отправка в облако и создание публичных ссылок на исследования
            res_list = Research.objects.filter(is_cloud_upload=False)
            if res_list:
                logger.info(f'[--- RESULT LIST ---] [{res_list}]')
                for res in res_list:
                    if res.ready_archive:
                        logger.info(f'[NEW ARCHIVE TO UPLOAD] [{res.ready_archive}] [{res.date_created}]')
                        start_time = datetime.now()
                        upload(file_path=f'/opt/dicom_converter/static/media/{res.ready_archive.name}',
                               email=res.user.email,
                               research_id=res.id)
                        end_time = datetime.now()
                        logger.info(f'[UPLOAD SUCCESS] [FINISHED TIME] [{end_time - start_time}]')
                sleep(5)
            else:
                logger.info(f'[--- EMPTY LIST ---]')
                sleep(5)

    except KeyboardInterrupt:
        sys.exit(0)
