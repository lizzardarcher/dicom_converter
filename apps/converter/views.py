from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import html_safe
from unidecode import unidecode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, View

from apps.converter.forms import ResearchUploadForm
from apps.converter.models import Research, UserSettings


class UploadResearchView(LoginRequiredMixin, SuccessMessageMixin, CreateView, View):
    model = Research
    form_class = ResearchUploadForm
    template_name = 'pages/upload_research.html'

    # def post(self, request):
    #     if request.method == 'POST':
    #         form = ResearchUploadForm(request.POST, request.FILES)
    #         if form.is_valid():
    #             form.save()
    #             return JsonResponse({'data': 'Data uploaded'})
    #
    #         else:
    #             return JsonResponse({'data': 'Something went wrong!!'})

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
