from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import html_safe
from django.views.decorators.csrf import csrf_exempt
from unidecode import unidecode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, View, TemplateView

from apps.converter.forms import ResearchUploadForm
from apps.converter.models import Research, UserSettings, TestResearch


class UploadResearchView(LoginRequiredMixin, SuccessMessageMixin, CreateView, View):
    model = Research
    form_class = ResearchUploadForm
    template_name = 'pages/upload_research.html'

    def get_context_data(self, **kwargs):
        context = super(UploadResearchView, self).get_context_data(**kwargs)
        try:
            research_avail_count = UserSettings.objects.filter(user=self.request.user).last().research_avail_count
        except AttributeError:
            research_avail_count = 0
        context.update({
            'research': Research.objects.filter(user=self.request.user).order_by('-date_created'),
            'research_avail_count': research_avail_count,
        })
        return context

    def get_success_url(self):
        return '/accounts/profile/'

    def get_success_message(self, cleaned_data):
        return (f"Архив [ {cleaned_data['raw_archive'].name} ] успешно обработан.\n"
                f"Данные томографа GALILEOS сконвертированы в формат DICOM\n"
                f"Ссылка на скачивание вскоре будет отправлена на вашу почту: {self.request.user.email}\n"
                f"Также вы можете скачать архив в личном кабинете")

    def form_valid(self, form):
        form.instance.user = self.request.user
        #  Переименовываем название raw_archive в латиницу
        name = form.cleaned_data['raw_archive'].name
        dots = int(str(name).count('.'))
        name = unidecode(str(name).strip().lower().replace(' ', '_', dots - 1))
        form.instance.raw_archive.name = name
        return super().form_valid(form)


class UploadView(TemplateView):
    """
    Класс для загрузки файлов с помощью CBV и AJAX.
    """
    template_name = 'pages/test_upload_research.html'

    @csrf_exempt
    def post(self, request):
        """
        Обработка POST-запроса для загрузки файла.
        """

        file = request.FILES.get('file')

        if file:
            # Сохранение файла в модели UploadFile
            upload_file = TestResearch(raw_archive=file)
            upload_file.save()

            # Создание сессии для хранения прогресса
            request.session['upload_progress'] = 0

            # Возвращение JSON-ответа с информацией о файле
            return JsonResponse({
                'success': True,
                'filename': upload_file.raw_archive.name,
                'file_size': upload_file.raw_archive.size,
                'file_url': upload_file.raw_archive.url,  # URL загруженного файла
            })
        else:
            # Обработка ошибки, если файл не был загружен
            return JsonResponse({
                'success': False,
                'error': 'Файл не был загружен.'
            })

@csrf_exempt
def progress_view(request):
    """
    Обработка запроса AJAX для обновления прогресса загрузки.
    """
    if request.method == 'POST':
        progress = request.POST.get('progress')
        # Обновление прогресса в сессии
        request.session['upload_progress'] = progress
        return JsonResponse({'progress': progress})
    else:
        return JsonResponse({'error': 'Invalid request method.'})


