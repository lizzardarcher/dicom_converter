import pydicom
import os


def merge_dicom(input_dir, output_filename):
    """Merges multiple DICOM images into a single file.

    Args:
      input_dir: The directory containing the DICOM images.
      output_filename: The name of the output file.
    """

    dicom_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.dcm'):
                if 'DICOMDIR.dcm' in file:
                    ...
                else:
                    dicom_files.append(os.path.join(root, file))


    # Sort the files by instance number (assuming they are already sorted)
    dicom_files.sort()

    # Create an empty list to store the datasets
    datasets = []

    # Loop through the DICOM files and read each one
    for filename in dicom_files:
        filepath = os.path.join(input_dir, filename)
        dataset = pydicom.dcmread(filepath)
        datasets.append(dataset)

    # Create a new dataset based on the first dataset
    merged_dataset = datasets[0]

    # Update the number of frames and pixel data
    merged_dataset.NumberOfFrames = len(datasets)
    merged_dataset.PixelData = b''.join([ds.PixelData for ds in datasets])

    # Save the merged dataset to a file
    pydicom.dcmwrite(output_filename, merged_dataset)

    print(output_filename)
    return output_filename

# Example usage:
# input_directory = "/home/ansel/PycharmProjects/dicom_converter/dcm/333"  # Replace with your directory
# output_file = "merged_dicom.dcm"
#
# merge_dicom(input_directory, output_file)
