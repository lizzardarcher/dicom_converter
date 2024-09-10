#!/usr/bin/env bash
# exit on error
set -o errexit

apt -y update
apt -y upgrade
apt -y install python3-dev
apt install -y default-libmysqlclient-dev
apt install -y build-essential
apt install -y pkg-config
apt install -y python3-pip
apt install libapache2-mod-wsgi-py3
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
