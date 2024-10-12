import os
import logging
import shutil

from django.core.mail import EmailMessage, DEFAULT_ATTACHMENT_MIME_TYPE
from django.conf import settings

from unidecode import unidecode


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    green = "\x1b[32;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def find_dir_by_name_part(start_path: str, target_dir_name: str):
    """Ищет директорию с частью заданного имени в указанной директории и ее подкаталогах.

    Args:
        start_path (str): Путь к стартовой директории для поиска.
        target_dir_name (str): Имя директории, которую нужно найти.

    Returns:
        str: Полный путь к найденной директории, или None, если директория не найдена.
    """

    for root, dirs, files in os.walk(start_path):
        for _ in dirs:
            if target_dir_name in _:
                return os.path.join(root, _)

    return None


def add_dcm_extension(directory):
    """
    Проходит по директории и добавляет ".dcm" к именам файлов,
    если у них нет расширения.
    """
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            # Проверяем, есть ли у файла расширение
            if not os.path.splitext(filename)[1]:
                # Добавляем ".dcm" к имени файла
                new_filename = filename + ".dcm"
                new_filepath = os.path.join(directory, new_filename)
                os.rename(filepath, new_filepath)
                print(f"Изменено имя файла: {filename} -> {new_filename}")


def search_file_in_dir(directory, string) -> str | None:
    """
    :param directory: Рекурсивный поиск по директории
    :param string: Название файла
    :return: Абсолютный путь до искомого файла или None
    """
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if string in filename:
                absolute_file_path = f"{root}/{filename}"
                print(absolute_file_path)
                return absolute_file_path
    return None


def add_ext_recursive(directory, new_extension):
    """
    Рекурсивно проходит по директории и добавляет новое расширение
    к именам файлов, у которых его нет.

    Args:
        directory (str): Путь к начальной директории.
        new_extension (str): Новое расширение файла (например, ".png").
    """
    counter = 0

    for root, dirs, files in os.walk(directory):
        for filename in files:
            base, ext = os.path.splitext(filename)
            if not ext:  # Проверяем, есть ли расширение
                new_filename = filename + new_extension
                old_filepath = os.path.join(root, filename)
                new_filepath = os.path.join(root, new_filename)
                os.rename(old_filepath, new_filepath)
                counter += 1
    print(f"Переименовано: {str(counter)} файлов")


def unidecode_recursive(directory):
    """
    Рекурсивно проходит по директории и добавляет новое расширение
    к именам файлов, у которых его нет.

    Args:
        directory (str): Путь к начальной директории.
        new_extension (str): Новое расширение файла (например, ".png").
    """
    counter = 0

    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            new_dir = unidecode(dir.replace(' ', ''))
            old_dir = os.path.join(root, dir)
            new_dir = os.path.join(root, new_dir)
            os.rename(old_dir, new_dir)
            counter += 1
            print(f"Переименован: {old_dir} ->  {new_dir}")

    print(f"Переименовано: {str(counter)} директорий")


def send_email_with_attachment(to_email, subject, body, file_path=None):
    # Создание экземпляра EmailMessage
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[to_email],
    )
    if file_path:
        # Добавление вложения
        email.attach_file(file_path, mimetype=DEFAULT_ATTACHMENT_MIME_TYPE)

    # Отправка письма
    email.send()


def copy_files(source_dir, destination_dir):
    """
    Copies files from a source directory to a destination directory.

    Args:
      source_dir (str): Path to the source directory.
      destination_dir (str): Path to the destination directory.

    Returns:
      str: Path to the destination directory.
    """

    # Ensure destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Iterate through files in the source directory
    for filename in os.listdir(source_dir):
        source_path = os.path.join(source_dir, filename)
        destination_path = os.path.join(destination_dir, filename)

        # Copy file if it's a regular file
        if os.path.isfile(source_path):
            shutil.copy2(source_path, destination_path)

    return destination_dir  # Return the destination directory


def find_folder(root_dir, folder_name):
    """
    Ищет папку с заданным именем в указанном каталоге и его подкаталогах.

    Args:
     root_dir (str): Путь к корневому каталогу для поиска.
     folder_name (str): Имя папки, которую нужно найти.

    Returns:
     str: Полный путь к найденной папке, или None, если папка не найдена.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if folder_name in dirnames:
            return os.path.join(dirpath, folder_name)
    return None


import patoolib


def archive_images(source_dir, archive_path, root_prefix='/opt/dicom_converter/static/media/converter/'):
    """
    Архивирует изображения из указанного каталога с сокращением пути внутри архива.

    Args:
      source_dir (str): Путь к каталогу с изображениями.
      archive_path (str): Путь к создаваемому архиву.
      root_prefix (str): Префикс пути, который нужно убрать из пути к файлам внутри архива.
    """

    # Создаем список файлов для архивации
    files_to_archive = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            # Сокращаем путь к файлу
            relative_path = os.path.relpath(os.path.join(root, file), root_prefix)
            files_to_archive.append(os.path.join(root, file))

    # Архивируем файлы с помощью patool
    patoolib.create_archive(archive_path, files_to_archive)
