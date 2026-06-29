import os
import shutil
import traceback


from django.core.mail import EmailMessage, DEFAULT_ATTACHMENT_MIME_TYPE
from django.conf import settings

from unidecode import unidecode

def find_dir_by_name_part(start_path: str, target_dir_name: str):
    """Ищет директорию с частью заданного имени в указанной директории и ее подкаталогах.

    Args:
        start_path (str): Путь к стартовой директории для поиска.
        target_dir_name (str): Имя директории, которую нужно найти.

    Returns:
        str: Полный путь к найденной директории, или None, если директория не найдена.
    """

    target_lower = target_dir_name.lower()
    for root, dirs, files in os.walk(start_path):
        for _ in dirs:
            if target_lower in _.lower():
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
                # print(f"Изменено имя файла: {filename} -> {new_filename}")


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
                # print(absolute_file_path)
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
    # print(f"Переименовано: {str(counter)} файлов")


def unidecode_recursive(directory):
    """
    Рекурсивно проходит по директории и добавляет новое расширение
    к именам файлов, у которых его нет.

    Args:
        directory (str): Путь к начальной директории.
    """
    counter = 0

    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            try:
                new_dir = unidecode(dir.replace(' ', ''))
                old_dir = os.path.join(root, dir)
                new_dir = os.path.join(root, new_dir)
                os.rename(old_dir, new_dir)
                # shutil.move(old_dir, new_dir)
                counter += 1
            except Exception as e:
                print(traceback.format_exc())
            # print(f"Переименован: {old_dir} ->  {new_dir}")

    # print(f"Переименовано: {str(counter)} директорий")


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


class ConversionError(Exception):
    """Ошибка конвертации с понятным сообщением для пользователя."""


RAR_EXTRACT_PROGRAMS = (
    '/usr/bin/unrar',
    '/usr/bin/rar',
    '/usr/bin/7z',
)


def _available_programs(programs: tuple[str, ...]) -> list[str]:
    return [program for program in programs if os.path.isfile(program)]


def extract_archive_safe(archive_path: str, output_dir: str) -> None:
    """Распаковывает архив, создавая output_dir; для RAR перебирает unrar/rar/7z."""
    from dicom_converter.logger.project_logger import logger

    os.makedirs(output_dir, exist_ok=True)
    archive_name = os.path.basename(archive_path).lower()

    if '.rar' in archive_name:
        programs = _available_programs(RAR_EXTRACT_PROGRAMS)
        if not programs:
            raise ConversionError(
                'На сервере не установлены утилиты для распаковки RAR (unrar, rar или 7z). '
                'Загрузите архив в формате ZIP или обратитесь в поддержку.'
            )

        errors = []
        for program in programs:
            try:
                patoolib.extract_archive(archive=archive_path, outdir=output_dir, program=program)
                logger.info(f'[EXTRACT] Успешно: {program} -> {output_dir}')
                return
            except Exception as exc:
                errors.append(f'{os.path.basename(program)}: {exc}')
                logger.warning(f'[EXTRACT] Не удалось через {program}: {exc}')

        raise ConversionError(
            'Не удалось распаковать RAR-архив. Файл может быть повреждён, защищён паролем '
            'или создан в неподдерживаемом формате. Попробуйте пересобрать архив в ZIP. '
            f'Детали: {"; ".join(errors)}'
        )

    if '.7z' in archive_name:
        program = '/usr/bin/7z'
        if not os.path.isfile(program):
            raise ConversionError(
                'На сервере не установлен 7z для распаковки .7z архивов. '
                'Загрузите архив в формате ZIP или RAR.'
            )
        try:
            patoolib.extract_archive(archive=archive_path, outdir=output_dir, program=program)
            logger.info(f'[EXTRACT] Успешно: {program} -> {output_dir}')
        except Exception as exc:
            raise ConversionError(
                f'Не удалось распаковать 7z-архив: {exc}'
            ) from exc
        return

    try:
        patoolib.extract_archive(archive=archive_path, outdir=output_dir)
        logger.info(f'[EXTRACT] Успешно: patoolib -> {output_dir}')
    except Exception as exc:
        raise ConversionError(
            f'Не удалось распаковать архив: {exc}'
        ) from exc


def find_galileos_vol_dir(start_path: str, target_dir_name: str = 'vol_0') -> str:
    """Возвращает путь к vol_0 или поднимает ConversionError с понятным текстом."""
    vol_dir = find_dir_by_name_part(start_path, target_dir_name)
    if vol_dir is None:
        raise ConversionError(
            f'В архиве не найдена папка «{target_dir_name}». '
            'Архив Galileos должен содержать директорию vol_0 с исходными изображениями. '
            'Убедитесь, что вы архивируете экспорт с томографа целиком, а не отдельные файлы.'
        )
    return vol_dir


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


def find_directory(directory_name, start_path="."):
    """
    Находит директорию с заданным именем и возвращает абсолютный путь к ней.

    Args:
      directory_name (str): Имя директории, которую нужно найти.
      start_path (str, optional): Начальный путь для поиска. По умолчанию - текущая директория.

    Returns:
      str: Абсолютный путь к найденной директории, или None, если директория не найдена.
    """
    for root, dirs, files in os.walk(start_path):
        if directory_name in dirs:
            return os.path.join(root, directory_name)
    return None  # Директория не найдена


def delete_file_recursively(directory, filename):
    """
    Удаляет файл с указанным именем рекурсивно во всей директории.

    Args:
      directory (str): Путь к директории, где нужно искать файл.
      filename (str): Имя файла, который нужно удалить.
    """
    for root, dirs, files in os.walk(directory):
        if filename in files:
            file_path = os.path.join(root, filename)
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Ошибка при удалении файла: {e}")
