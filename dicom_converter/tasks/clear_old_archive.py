import os
import sys
import time
from datetime import datetime, timedelta

dirs_to_check = ['/opt/dicom_converter', '/opt/dicom_converter/static/media/converter/ready']


def delete_old_archives(directory, days_threshold=2):
    """
    Удаляет архивы (zip, rar, dcm) в указанной директории,
    если они были созданы более `days_threshold` дней назад.

    Args:
        directory (str): Путь к директории.
        days_threshold (int): Количество дней, после которого архивы считаются старыми.
    """

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        # Проверяем, является ли файл архивом (ZIP или RAR)
        if filename.endswith((".zip", ".rar", ".dcm")):
            try:
                # Получаем время создания файла
                file_creation_time = datetime.fromtimestamp(os.path.getctime(filepath))
                print(f'[Найден файл] [{filename}] [{file_creation_time}]')

                # Проверяем, старше ли файл, чем `days_threshold` дней
                if file_creation_time < datetime.now() - timedelta(days=days_threshold):
                    os.remove(filepath)
                    print(f"Удален файл: {filepath}")
            except Exception as e:
                print(f"Ошибка при обработке файла {filepath}: {e}")


if __name__ == '__main__':
    try:
        while True:
            for _ in dirs_to_check:
                delete_old_archives(_)
                time.sleep(3)
    except KeyboardInterrupt:
        sys.exit(0)