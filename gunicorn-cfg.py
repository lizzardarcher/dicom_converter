# # -*- encoding: utf-8 -*-

command = '/opt/dicom_converter/env/bin/gunicorn'
pythonpath = '/opt/dicom_converter'
bind = '0.0.0.0'
workers = 2
accesslog = '-'
loglevel = 'debug'
capture_output = True
enable_stdio_inheritance = True
reload = True