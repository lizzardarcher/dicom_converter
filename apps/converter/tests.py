# import time
#
# from django.test import TestCase
# import patoolib
# # Create your tests here.
# start_time = time.time()
# patoolib.create_archive(
#     archive='testo.zip',
#     filenames=('/home/ansel/PycharmProjects/dicom_converter/db.sqlite3',))
# end_time = time.time()
# print(f'{end_time - start_time} seconds')
#
# start_time = time.time()
# patoolib.create_archive(
#     archive='testo.rar',
#     filenames=('/home/ansel/PycharmProjects/dicom_converter/db.sqlite3',))
# end_time = time.time()
# print(f'{end_time - start_time} seconds')
import os
import re

import os
import re

import os
import re
import shutil


# def rename_dcm_files(source_directory, destination_directory):
#     """
#     Переименовывает файлы .dcm в обратном порядке, сохраняя их в новую директорию.
#
#     Args:
#       source_directory (str): Путь к исходной директории, где находятся файлы.
#       destination_directory (str): Путь к целевой директории, куда будут записаны переименованные файлы.
#     """
#     # Находим максимальное число в именах файлов
#     max_number = 0
#     for root, dirs, files in os.walk(source_directory):
#         for filename in files:
#             match = re.search(r'IM(\d+).dcm', filename)
#             if match:
#                 number = int(match.group(1))
#                 max_number = max(max_number, number)
#     print(max_number)
#     # Создаем целевую директорию, если она не существует
#     os.makedirs(destination_directory, exist_ok=True)
#
#     # Переименовываем файлы в обратном порядке
#     for i in range(max_number, 0, -1):
#         filename = f"IM{i:06d}.dcm"
#         for root, dirs, files in os.walk(source_directory):
#             for j, f in enumerate(files):
#                 match = re.search(r'IM(\d+).dcm', f)
#                 if match and int(match.group(1)) == i:
#                     old_path = os.path.join(root, f)
#                     new_path = os.path.join(destination_directory, filename)
#                     # print(old_path, new_path)
#                     shutil.copy2(old_path, new_path)  # Копируем файл в новую директорию
#                     break
#
#
# # Пример использования
# source_directory = "/home/ansel/Загрузки/multifile_galileos_pro_research_developer_20241021130353/20241021130102/PT000000/ST000000"  # Замените на путь к вашей исходной директории
# destination_directory = "/home/ansel/Загрузки/multifile_galileos_pro_research_developer_20241021130353/20241021130102"  # Замените на путь к вашей целевой директории
# rename_dcm_files(source_directory, destination_directory)



