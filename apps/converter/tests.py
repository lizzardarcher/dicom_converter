from django.test import TestCase
import patoolib
# Create your tests here.
patoolib.create_archive(
    archive='testo.zip',
    filenames=('/home/ansel/PycharmProjects/dicom_converter/converter/extract_dir/0000ab5ef63e6d33_vol_0_tzFCV9v/ready',))
