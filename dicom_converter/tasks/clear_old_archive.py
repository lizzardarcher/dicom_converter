import os
import shutil
import sys
import time
from datetime import datetime, timedelta


from django.conf import settings

from dicom_converter.orm import django_orm  # noqa: F401 — инициализация Django ORM
from apps.converter.models import Research
from dicom_converter.logger.project_logger import logger

ARCHIVE_EXTENSIONS = ('.zip', '.rar', '.7z', '.dcm')
RAW_DAYS_THRESHOLD = 7
EXTRACT_DIR_DAYS_THRESHOLD = 7
TMP_DAYS_THRESHOLD = 1
READY_DAYS_THRESHOLD = 30
SLEEP_INTERVAL = 60


def _media_converter_dir(*parts):
    return os.path.join(str(settings.MEDIA_ROOT), 'converter', *parts)


def _is_archive_file(filename):
    return filename.lower().endswith(ARCHIVE_EXTENSIONS)


def _is_older_than(path, days_threshold):
    creation_time = datetime.fromtimestamp(os.path.getctime(path))
    return creation_time < datetime.now() - timedelta(days=days_threshold)


def _get_pending_cloud_upload_basenames():
    basenames = set()
    for research in Research.objects.filter(is_cloud_upload=False).exclude(ready_archive=''):
        if research.ready_archive:
            basenames.add(os.path.basename(research.ready_archive.name))
    return basenames


def delete_old_files(directory, days_threshold, *, can_delete=None, on_deleted=None):
    """Рекурсивно удаляет архивные файлы старше days_threshold дней."""
    if not os.path.isdir(directory):
        return

    for root, _, files in os.walk(directory):
        for filename in files:
            if not _is_archive_file(filename):
                continue

            filepath = os.path.join(root, filename)
            if not _is_older_than(filepath, days_threshold):
                continue
            if can_delete and not can_delete(filepath, filename):
                continue

            try:
                os.remove(filepath)
                logger.info(f'Удален файл: {filepath}')
                if on_deleted:
                    on_deleted(filepath, filename)
            except Exception as e:
                logger.info(f'Ошибка при обработке файла {filepath}: {e}')


def on_ready_file_deleted(filepath, filename):
    rel_path = f'converter/ready/{filename}'
    Research.objects.filter(ready_archive=rel_path).update(ready_archive='')


def clear_missing_ready_references():
    ready_dir = _media_converter_dir('ready')
    for research in Research.objects.exclude(ready_archive='').exclude(ready_archive__isnull=True):
        filepath = os.path.join(str(settings.MEDIA_ROOT), research.ready_archive.name)
        if not os.path.isfile(filepath):
            Research.objects.filter(pk=research.pk).update(ready_archive='')


def delete_old_directories(directory, days_threshold):
    """Удаляет поддиректории старше days_threshold дней."""
    if not os.path.isdir(directory):
        return

    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if not os.path.isdir(path):
            continue
        if not _is_older_than(path, days_threshold):
            continue

        try:
            shutil.rmtree(path)
            logger.info(f'Удалена директория: {path}')
        except Exception as e:
            logger.info(f'Ошибка при удалении директории {path}: {e}')


def can_delete_ready_file(filepath, filename):
    """Не удалять ready-архив, пока он ожидает загрузки в облако."""
    return filename not in _get_pending_cloud_upload_basenames()


def run_cleanup_cycle():
    raw_dir = _media_converter_dir('raw')
    extract_dir = _media_converter_dir('extract_dir')
    ready_dir = _media_converter_dir('ready')
    tmp_dir = _media_converter_dir('tmp')

    delete_old_files(raw_dir, RAW_DAYS_THRESHOLD)
    delete_old_directories(extract_dir, EXTRACT_DIR_DAYS_THRESHOLD)
    delete_old_directories(tmp_dir, TMP_DAYS_THRESHOLD)
    delete_old_files(tmp_dir, TMP_DAYS_THRESHOLD)
    delete_old_files(
        ready_dir,
        READY_DAYS_THRESHOLD,
        can_delete=can_delete_ready_file,
        on_deleted=on_ready_file_deleted,
    )
    clear_missing_ready_references()


if __name__ == '__main__':
    try:
        while True:
            run_cleanup_cycle()
            time.sleep(SLEEP_INTERVAL)
    except KeyboardInterrupt:
        sys.exit(0)
