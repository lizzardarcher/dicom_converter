$(document).ready(function () {

    var raw_archive = document.getElementById('id_raw_archive');
    var is_one_file = document.getElementById('flexSwitchCheckDefault2');
    var submit_btn = document.getElementById('submit_btn')
    var pgb = $('#progress_bar');
    pgb.hide();

    let lang = 'ru'
    let currentLocation = String(window.location);
    if (currentLocation.includes('/en/')) {
        lang = 'en'
    }

    $('#upload_form').submit(function (event) {
        event.preventDefault();

        var fileInput = $('#id_raw_archive')[0];
        var file = fileInput.files[0];
        var errorDiv = $('#errorMessages'); // Добавьте этот элемент в ваш HTML
        // Очистка предыдущих ошибок
        errorDiv.empty();

        // Проверка на пустое значение
        if (file === undefined) {
            errorDiv.append('<div class="alert alert-danger" role="alert">Пожалуйста, выберите файл.</div>');
            return false;
        }

        // Проверка размера файла
        if (file.size > 700 * 1024 * 1024) {
            errorDiv.append('<div class="alert alert-danger" role="alert">Размер файла превышает 700 МБ.</div>');
            return false;
        }

        // Проверка расширения файла
        var allowedExtensions = ['zip', 'rar'];
        var fileExtension = file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
            errorDiv.append('<div class="alert alert-danger" role="alert">Допустимые расширения: ZIP, RAR.</div>');
            return false;
        }


        var formData = new FormData(this);
        var csrftoken = $('input[name=csrfmiddlewaretoken]').val();

        $.ajax({
            url: '/' + lang + '/upload_research',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': csrftoken
            },
            xhr: function () {
                var xhr = new window.XMLHttpRequest();
                console.log(xhr)
                xhr.upload.addEventListener('progress', function (event) {
                    if (event.lengthComputable) {
                        var percentComplete = (event.loaded / event.total) * 100;
                        $('#progressBarValue').css('width', percentComplete + '%');
                        //$('#progress_bar').html('Загружено: '+ Math.floor(percentComplete) + '%');
                        $('#progress_text').html('Загружено: ' + Math.floor(percentComplete) + '%');
                        // Вызов функции обновления прогресса
                        $.ajax({
                            url: '/' + lang + '/progress/',
                            type: 'POST',
                            data: {'progress': percentComplete},
                            success: function (data) {
                                console.log(data);
                                return false;
                            }
                        });
                    }
                });
                raw_archive.disabled = true;
                is_one_file.disabled = true;
                submit_btn.disabled = true;
                pgb.show();
                return xhr;
            },
            success: function (data) {
                // Обработка успешной загрузки
                // Переход на index.html с успешным сообщением
                console.log(data)
                window.location.href = '/?success=true&message=' + encodeURIComponent((
                    "Данные томографа GALILEOS сконвертированы в формат DICOM " +
                    "Ссылка на скачивание вскоре будет отправлена на вашу почту." +
                    " Также вы можете скачать архив в личном кабинете"
                ));
                return false;
            },
            error: function (error) {
                // Обработка ошибки
                // Обработка ошибки
                if (error.status === 504) {
                    // Ошибка 504: Gateway Timeout
                    window.location.href = '/?success=true&message=' + encodeURIComponent((
                        "Данные томографа GALILEOS сконвертированы в формат DICOM " +
                        "Ссылка на скачивание вскоре будет отправлена на вашу почту." +
                        " Также вы можете скачать архив в личном кабинете"
                    ));
                } else {
                    // Другие ошибки
                    console.error(error);
                    $('#errorMessages').append('<div class="alert alert-danger" role="alert">Произошла ошибка при загрузке файла. Пожалуйста, попробуйте позже.</div>');
                }
                console.error(error);
                return false;
            }
        });
    });
});

