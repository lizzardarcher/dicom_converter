import os


def find_directory(start_path: str, target_dir_name: str):
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

# # Пример использования
# start_directory = "/home/ansel/PycharmProjects/dicom_converter"
# target_directory = "vol_0"
#
# found_path = find_directory(start_directory, target_directory)
#
# if found_path:
#     print(f"Директория '{target_directory}' найдена: {found_path}")
# else:
#     print(f"Директория '{target_directory}' не найдена.")