import os


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


import os

import os

def rename_files_recursive(directory, new_extension):
    """
    Рекурсивно проходит по директории и добавляет новое расширение
    к именам файлов, у которых его нет.

    Args:
        directory (str): Путь к начальной директории.
        new_extension (str): Новое расширение файла (например, ".png").
    """

    for root, dirs, files in os.walk(directory):
        for filename in files:
            base, ext = os.path.splitext(filename)
            if not ext:  # Проверяем, есть ли расширение
                new_filename = filename + new_extension
                old_filepath = os.path.join(root, filename)
                new_filepath = os.path.join(root, new_filename)
                os.rename(old_filepath, new_filepath)
                print(f"Переименовано: {old_filepath} -> {new_filepath}")



