__title__ = "glx2dicom"
__version__ = "0.1"
__author__ = "Max Nikulin"
__email__ = "manikulin@gmail.com"
__description__ = \
    """Convert Sirona GALAXIS (GALILEOS Viewer) CBCT format to DICOM"""
__license__ = "GPLv3+"
__copyright__ = "Copyright (C) 2022 Max Nikulin"

import datetime
import gzip

from lxml import etree
from pathlib import Path
from pydicom import uid, datadict
from pydicom.dataset import FileDataset
from pydicom.dataset import FileMetaDataset
from pydicom.fileset import FileSet
import re
from typing import Any, Dict, List


usage = """%(prog)s --tag PatientName='Surname^Name' \\
           --tag PatientBirthDate='19700101' \\
           [--tag TAG=VALUE]... SRC_DIR OUT_DIR
   or: %(prog)s [--help | --version]
"""

version = f"""%(prog)s {__version__}
{__copyright__}
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
"""

default_dicom_attrs = {
    # Random UUID obtained using ``uid.generate_uid(None)``
    'ImplementationClassUID': '2.25.88075347621178512596802224299896711910',
    'SpecificCharacterSet': 'ISO_IR 100',
    'TransferSyntaxUID': uid.ExplicitVRLittleEndian,
    # PS3.3 C.7.1 patient
    # No UID
    # Likely encoded in ``.gwg` files
    'PatientName': 'Test^Firstname',
    'PatientID': '1234456789',
    # TODO (0018, 5100) PatientPosition
    # PS3.3 C.7.2 study
    'StudyDescription': 'Dental CBCT Study',
    # Physisian
    # PS3.3 C.7.3 series
    'Modality': 'CT',
    'SeriesNumber': "1",
    'SeriesDescription': "CT series",
    # Unsure, perhaps "ORIGINAL" would be for images from which
    # CT is reconstructed.
    'ImageType': ['DERIVED', 'PRIMARY'],
    'NumberOfFrames': 1,
    # PS3.3 C.7.6 Image
    # TODO 'PatientOrientation'
    # PS3.3 C.7.6.2, 10.7
    # Unsure, but do not see obviously wrong orientation.
    'ImageOrientationPatient': [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    # PS3.3 C7.6.3, C7.6.3.3
    'SamplesPerPixel': 1,
    'PhotometricInterpretation': 'MONOCHROME2',  # 2 bytes per pixel greyscale
    # SightViewer-21.1.1 can not handle 0 (unsigned) 16 bit images
    'PixelRepresentation': 1,  # 2's component (unsigned)
    'BitsAllocated': 16  # multiple of 8
}

uid_prefix = None
"""UID prefix used to generate e.g. image identifiers
``None``
    UUID (default since I have not registered prefix),
``""``
    prefix registered for ``pydicom``.
"""


def read_fbp_params(ct_dir: Path) -> Dict[str, Any]:
    with gzip.open(ct_dir / ct_dir.name, "rb") as f:
        tree = etree.fromstring(f.read())

    # Other <LibParams> children:
    # - TimeStamp: no seconds
    # - SequenceID
    # - CrossHairX, Y, Z.
    assert tree.tag == "FBPParams"
    params = tree.find("LibParams")
    assert params is not None
    assert params.find("ZoomFactor").text == "1"
    # <DEVICEPLUGIN> (parsed from <ScanParamsXml> text)
    # attributes that might be useful:
    # - deviceid
    # - dx89serialsno
    # - p2kserialno
    # - kv
    # - ma
    # - xraypulsewidth
    scan = etree.fromstring(params.find("ScanParamsXml").text)
    assert scan is not None
    assert scan.tag == "DEVICEPLUGIN"
    # print(etree.tostring(scan, pretty_print=True, encoding="unicode"))
    image = scan.find('IMAGEDESCRIPTION/IMAGE')
    assert image is not None

    img_date = image.attrib['takedate']
    img_time = image.attrib['taketime']
    assert re.match("[0-9]{4}-[0-9]{2}-[0-9]{2}", img_date)
    assert re.match("[0-9]{2}:[0-9]{2}:[0-9]{2}", img_time)
    img_date = re.sub("-", "", img_date)
    img_time = re.sub(":", "", img_time)

    retval = {}

    # PS3.3 C.7.6 Image
    retval['ContentDate'] = img_date
    retval['ContentTime'] = img_time

    # PS3.3 C.7.6.3 Image Pixel Module
    # PS3.3 C.7.6.3.3 Image Pixel Description Macro
    rows = int(params.find('VolSizeX').text)
    assert rows > 0
    columns = int(params.find('VolSizeY').text)
    assert columns > 0
    retval['Rows'] = rows
    retval['Columns'] = columns
    # 14, but really 12
    bits = int(params.find('ImageInBitDepth').text)
    assert bits > 8 and bits <= 16
    value_max = int(params.find('VoxelValueMax').text)
    assert value_max < (2 << bits)
    retval['BitsStored'] = bits
    # PS3.3 C.7.6.3.3
    # and PS3.5 8.1.1 Pixel Data Encoding of Related Data Elements
    retval['HighBit'] = bits - 1

    # PS3.3 C.7.6.2, 10.7
    retval['PixelSpacing'] = [
        float(params.find('VoxelSizeX').text),
        float(params.find('VoxelSizeY').text)]
    thickness = float(params.find('VoxelSizeZ').text)
    assert thickness > 0.0
    retval['SliceThickness'] = thickness
    retval['SpacingBetweenSlices'] = thickness
    z = float(params.find('CenterZ').text)
    retval['ImagePositionPatient'] = [
        float(params.find('CenterX').text)
        - 0.5*(columns - 1)*retval['PixelSpacing'][0],
        float(params.find('CenterY').text)
        - 0.5*(rows - 1)*retval['PixelSpacing'][1],
        z]
    retval['SliceLocation'] = z  # likely unused by applications

    retval['SeriesDate'] = img_date
    retval['SeriesTime'] = img_time

    scan_id = params.find("ScanID").text
    assert scan_id is not None
    # PS3.3 C.7.2 study
    # Unsure, perhaps a scan may contain more than single volume
    retval['StudyID'] = scan_id
    retval['StudyDate'] = img_date
    retval['StudyTime'] = img_time

    retval['FileSetID'] = scan_id

    # PS3.3 C.11.2.1.2.1 Note 4
    # Look Up Tables and Presentation States
    # > VOI LUT Module
    # > Window Center and Window Width
    # > Default LINEAR Function
    #
    # Added with hope that sight viewer will use it to construct
    # default transfer function instead of displaying white brick at startup
    x1 = int(params.find('VoxelValueMin').text)
    assert x1 >= 0
    x2 = int(params.find('VoxelValueMax').text)
    assert x2 > x1
    retval['WindowCenter'] = (x1 + x2 + 1)//2
    retval['WindowWidth'] = x2 - x1 + 1
    # FIXME I am completely unsure in the following values,
    # they are taken from a DICOM file sample,
    # but they makes SightViewer behavior better.
    # Otherwise it displays a white brick when a CT is loaded
    # and it is necessary to adjust transfer function.
    retval['RescaleIntercept'] = -1000
    retval['RescaleType'] = 'HU'
    retval['RescaleSlope'] = 1.0

    return retval


def glx2dicom(srcdir: Path, dstdir: Path, dicom_attrs) -> None:
    # It seems trailing "/" does not matter.
    attrs = dicom_attrs.copy()

    media_storage_sop_class_uid = attrs.pop('MediaStorageSOPClassUID', None)
    sop_class_uid = attrs.pop('SOPClassUID', media_storage_sop_class_uid)
    if not sop_class_uid:
        sop_class_uid = uid.CTImageStorage
    elif (
            media_storage_sop_class_uid and
            sop_class_uid != media_storage_sop_class_uid):
        raise ValueError(
            'SOPClassUID != MediaStorageSOPClassUID',
            (sop_class_uid, media_storage_sop_class_uid))

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = sop_class_uid
    ds = FileDataset(
        None, {},
        file_meta=file_meta,
        is_implicit_VR=False,
        is_little_endian=True)
    # Not necessary in the case of
    #     ds.save_as(ds.filename, write_like_original=False)
    # It seems ``FileSet.write()`` ensures proper format as well.
    # ds.preamble = b'\0'*128

    # PS3.3 C.12
    # C.12.1.1.1.1 should be equal to File Meta Information header
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

    # ``FileSet`` attribute, image values are generated using UID prefix
    media_storage_sop_instace_uid = attrs.pop(
        'MediaStorageSOPInstanceUID', None)
    sop_instance_uid = attrs.pop(
        'SOPInstanceUID', media_storage_sop_instace_uid)
    if not sop_instance_uid:
        sop_instance_uid = uid.generate_uid(uid_prefix)
    elif (
            media_storage_sop_instace_uid and
            sop_instance_uid != media_storage_sop_instace_uid):
        raise ValueError(
            'SOPInstanceUID != MediaStorageSOPInstanceUID',
            (sop_instance_uid, media_storage_sop_instace_uid))

    # :dcm:`part03/sect_C.7.4.html` PS3.3 C.7.4 Frame of Reference Module
    # Identifies frame of reference withing a series.
    for tag in [
            'StudyInstanceUID', 'SeriesInstanceUID', 'FrameOfReferenceUID']:
        value = attrs.pop(tag, None) or uid.generate_uid(uid_prefix)
        setattr(ds, tag, value)

    fs = FileSet()
    fs.MediaStorageSOPInstanceUID = sop_instance_uid

    # PS3.3 C.12
    instance_creation_date = attrs.pop('InstanceCreationDate', '')
    instance_creation_time = attrs.pop('InstanceCreationTime', '')
    if (not instance_creation_date) and (not instance_creation_date):
        dt = datetime.datetime.now()
        instance_creation_date = dt.strftime("%Y%m%d")
        instance_creation_time = dt.strftime("%H%M%S.%f")
    ds.InstanceCreationDate = instance_creation_date
    ds.InstanceCreationTime = instance_creation_time

    for k, v in attrs.items():
        tag1 = (datadict.tag_for_keyword(k) & 0xffff0000) >> 16
        obj = ds
        if tag1 == 0x0002:
            obj = file_meta
        elif tag1 == 0x0004:
            obj = fs
        setattr(obj, k, v)

    transfer_syntax_uid = attrs['TransferSyntaxUID']
    photometric_interpretation = attrs['PhotometricInterpretation']
    slice_spacing = attrs['SpacingBetweenSlices']
    z_center = attrs['ImagePositionPatient'][2]
    pixel_bytes, bits_allocated_remnant = divmod(attrs['BitsAllocated'], 8)
    assert bits_allocated_remnant == 0
    data_length = attrs['Rows']*attrs['Columns']*pixel_bytes

    src = sorted(src_dir.glob(src_dir.name + '_[0-9]*[0-9]'))
    if not len(src) > 0:
        raise RuntimeError(f'No files found in {src_dir:r}', src_dir)
    z_base = z_center - 0.5*slice_spacing*(len(src) + 1)

    i = 1
    for f in src:
        # print(f'{i:3d} {f}')

        # It seems compressing image or adding dataset to fileset
        # resets some attributes
        ds.PhotometricInterpretation = photometric_interpretation
        file_meta.TransferSyntaxUID = transfer_syntax_uid
        file_meta.MediaStorageSOPInstanceUID = uid.generate_uid(uid_prefix)
        # PS3.3 C.12
        # C12.1.1.1.1 should be equal to File Meta Information header
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        # PS3.3 C.7.6 Image
        ds.InstanceNumber = f"{str(i)}"  # Earlier "Image Number"
        z = z_base + i*slice_spacing
        ds.ImagePositionPatient[2] = z
        ds.SliceLocation = z  # likely unused by applications
        with gzip.open(f, "rb") as img:
            data = img.read()
        assert len(data) == data_length
        ds.PixelData = data
        # Attempt to set ``SmallestImagePixelValue``
        # and ``LargestImagePixelValue`` causes
        #     TypeError: object of type 'numpy.int16' has no len()
        # on writing DICOM file. It does not matter if ``pixel_array``
        # is obtained from ``ds`` or created explicitly.
        # pixel_type = numpy.dtype(numpy.float32)
        # pixel_type.newbyteorder('<')
        # pixel_array = numpy.frombuffer(data, pixel_type)
        # ds.SmallestImagePixelValue = pixel_array.min()
        # ds.LargestImagePixelValue = pixel_array.max()
        # ds.PixelData = pixel_array.tobytes()

        # Docs mention 'pylibjpeg' plugin as well.
        # ds.compress(uid.RLELossless)
        # ds.compress(uid.RLELossless, encoding_plugin='gdcm')
        # ds.compress(uid.RLELossless, encoding_plugin='pylibjpeg')

        # Adds to a temporary directory at first.
        # It seems there is no option to control it.
        fs.add(ds)
        # TODO Should 'Rows' and 'Columns' attributes be added
        # to each image directory record?
        i += 1
    fs.write(dstdir)


def create_argument_parser():
    from argparse import ArgumentParser, RawDescriptionHelpFormatter
    parser = ArgumentParser(
        usage=usage,
        description=__description__,
        # Do not wrap --version
        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-V", "--version", action="version", version=version)
    parser.add_argument(
        "--tag", metavar="DICOM_TAG=VALUE",
        default=[], action="append",
        help="set or override DICOM tag")
    parser.add_argument(
        "src_dir", metavar="SRC_DIR",
        help='Directory with source CT images'
        ', "ID_vol_0" adjucent to the "ID.gwg" file')
    parser.add_argument(
        "dst_dir", metavar="DST_DIR",
        help='Directory to write the result DICOMDIR and images')
    return parser


def cli_tags2dict(tags: List[str]):
    retval = {}
    errors = []
    for kv in tags:
        k, v = kv.split("=", 2)
        try:
            datadict.dictionary_VR(k)
            # TODO convert integer values
            retval[k] = v
        except (KeyError, ValueError):
            errors.append(f'Unknown DICOM tag: {kv!r}')
    return retval, errors


def readme():
    """Print description intended for ``README.rst`` file.
    - Merge the module docstring with disclaimer and license statement.
    - Check metadata consistency.
    Usage::
        python3 -c 'from glx2dicom import readme; print(readme())'
    """
    title, usage_par, usage_cmd, body = __doc__.split(sep='\n\n', maxsplit=3)
    assert title == f'{__title__} - {__description__}'
    use = re.sub(r'\n.*--version.*\n', '', usage)
    assert re.sub(r'^ *', '', usage_cmd, flags=re.MULTILINE) == re.sub(
        r'^ *', '',
        use % dict(prog=f'python3 {__title__}.py'),
        flags=re.MULTILINE)
    title_bar = re.sub('.', '=', title)
    # print('\n'.join([
    #     title_bar, title, title_bar, '', usage_par,
    #     '', usage_cmd, '', body, '']),
    #     end='')
    # print(
    #     re.sub('<([^>]+)>', '\\1', version).strip()
    #     .replace('\n', '\n\n') % dict(prog=__title__))


if __name__ == '__main__':
    parser = create_argument_parser()
    args = parser.parse_args()
    src_dir = Path(args.src_dir)
    # ``collections.ChainMap(dicom_attrs, default_dicom_attrs)``
    # would not work because ``pop(key)`` removes element
    # from first dict only and next time the ``key`` may be obtained
    # from second dict.
    dicom_attrs = default_dicom_attrs.copy()
    glx_attrs = read_fbp_params(src_dir)
    dicom_attrs.update(glx_attrs)

    cli_attrs, errors = cli_tags2dict(args.tag)
    if errors:
        # "%(prog)s" is not supported here
        parser.error("\n".join(errors))
    dicom_attrs.update(cli_attrs)

    # TODO --verbose option
    # from pprint import pprint
    # pprint(dicom_attrs)

    start_time = datetime.datetime.now()
    glx2dicom(src_dir, Path(args.dst_dir), dicom_attrs)
    finish_time = datetime.datetime.now()
    # time spent
    print(f'[glx2dicom] [finished in] [{str(finish_time - start_time)}] ')