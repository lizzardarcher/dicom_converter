# Web-сервис по конвертации данных с томографа GALILEOS/SIRONA в формат DICOM

Данный веб-сервис предназначен для конвертации данных, полученных с томографа GALILEOS от компании SIRONA, в стандартный формат DICOM (Digital Imaging and Communications in Medicine). Формат DICOM позволяет хранить и обмениваться медицинскими изображениями, что делает его идеальным для интеграции с различными медицинскими системами и программным обеспечением.

## Особенности

- Конвертация данных в стандартный формат DICOM.
- Удобный интерфейс для загрузки данных.

## Стек технологий

- Python == 3.12
- Django >= 5.0
- Gunicorn
- Nginx
- MySQL (или другая база данных)

## Установка и развертывание

Вот шаги для установки и развертывания приложения на сервере с использованием Gunicorn и Nginx.

### 1. Подготовка сервера

Обновите пакеты на сервере:

> apt -y update
>
> apt -y upgrade

### 2. Установка зависимостей

Выполните следующие команды для установки необходимых пакетов:

> apt -y install python3-dev
>
> apt install -y default-libmysqlclient-dev
>
> apt install -y build-essential
>
> apt install -y pkg-config
>
> apt install -y python3-pip

### 3. Клонирование репозитория

Клонируйте репозиторий вашего проекта с GitHub (или другого источника):
> git clone https://github.com/lizzardarcher/dicom_converter.git

> cd ваш_репозиторий

### 4. Установка зависимостей Python

Установите зависимости Python из файла requirements.txt:

> pip install -r requirements.txt

### 5. Настройка базы данных

Настройте вашу базу данных (например, MySQL) и обновите настройки в файле settings.py вашего Django проекта. 

> python3 manage.py migrate

### 5. Настройка MAIL

settings.py
> EMAIL_HOST_PASSWORD = https://account.mail.ru/user/2-step-auth/passwords/

#### SMTP для отправки файлов большого размера

###### python code
> import smtplib    
> 
> smtp = smtplib.SMTP('localhost:8000')    
> 
> smtp.ehlo()    
> 
> max_limit_in_bytes = int( smtp.esmtp_features['size'] )


###### terminal
> apt install postfix
>
> postconf message_size_limit
>
> postconf -e 'message_size_limit = 704857600'  (700MB)
>
> service postfix reload

### 6. Запуск Gunicorn

Запустите Gunicorn для вашего проекта:

> gunicorn --workers 3 myproject.wsgi:application --bind unix:/path/to/your/project/myproject.sock

Замените myproject на имя вашего проекта.

### 7. Настройка Nginx

Создайте файл конфигурации для вашего сайта в Nginx:sudo nano /etc/nginx/sites-available/myproject
Добавьте следующую конфигурацию:

    server {
        listen 80;
        server_name ваш_домен_или_IP; # Замените на ваш домен или IP
    
        location = /favicon.ico { access_log off; log_not_found off; }
    
        location /static/ {
            alias /path/to/your/project; # Замените на путь к вашим статическим файлам
        }
    
        location /media/ {
                alias /path/to/your/project; # Замените на путь к вашим статическим файлам
        }
    
        location / {
            include proxy_params;
            proxy_pass http://unix:/path/to/your/project/myproject.sock; # Убедитесь, что путь совпадает
        }
    }
Сделайте символическую ссылку для активации конфигурации:sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled
### 8. Проверка конфигурации Nginx

Проверьте конфигурацию Nginx на наличие ошибок:sudo nginx -t
### 9. Перезапуск Nginx

Перезапустите Nginx, чтобы применить изменения:sudo systemctl restart nginx
### 10. (Опционально) Запуск Gunicorn как службы

Создайте файл службы для Gunicorn:sudo nano /etc/systemd/system/gunicorn.service
Добавьте следующую конфигурацию:
> [Unit]
> Description=gunicorn daemon
> After=network.target
> 
> [Service]
> User=ваш_пользователь  # Замените на ваше имя пользователя
> Group=www-data
> WorkingDirectory=/path/to/your/project  # Путь к вашему проекту
> ExecStart=/path/to/your/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/path/to/your/project/myproject.sock myproject.wsgi:application
> 
> [Install]
> WantedBy=multi-user.target

Запустите и включите службу Gunicorn:
> sudo systemctl enable gunicorn

> sudo systemctl start gunicorn

## Заключение

Теперь ваш веб-сервис по конвертации данных с томографа GALILEOS/SIRONA в формат DICOM развернут и доступен для использования. 
Вы можете получать доступ к интерфейсу по адресу вашего домена или IP-адресу сервера.

# ❌ Доступ к коду самого конвертера закрыт ❌

