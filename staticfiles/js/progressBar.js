$(document).ready(function () {
    $('#uploadForm').submit(function (event) {
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
            url: '/ru/upload/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': csrftoken
            },
            xhr: function () {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', function (event) {
                    if (event.lengthComputable) {
                        var percentComplete = (event.loaded / event.total) * 100;
                        $('#progressBarValue').css('width', percentComplete + '%');
                        // Вызов функции обновления прогресса
                        $.ajax({
                            url: '/ru/progress/',
                            type: 'POST',
                            data: {'progress': percentComplete},
                            success: function (data) {
                                console.log(data);
                                return false;
                            }
                        });
                    }
                });
                return xhr;
            },
            success: function (data) {
                // Обработка успешной загрузки
                // Переход на index.html с успешным сообщением
                console.log(data)
                window.location.href = '/?success=true&message=' + encodeURIComponent('Файл успешно загружен!');
                return false;
            },
            error: function (error) {
                // Обработка ошибки
                console.error(error);
                return false;
            }
        });
    });
});

