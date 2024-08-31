from unidecode import unidecode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView

from apps.converter.forms import ResearchUploadForm
from apps.converter.models import Research


class UploadResearchView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Research
    form_class = ResearchUploadForm
    template_name = 'pages/upload_research.html'

    def get_context_data(self, **kwargs):
        context = super(UploadResearchView, self).get_context_data(**kwargs)
        context.update({
            'research': Research.objects.filter(user=self.request.user),
        })
        return context

    def get_success_url(self):
        return '/accounts/profile/'

    def get_success_message(self, cleaned_data):
        return f"Архив успешно обработан {cleaned_data['raw_archive'].name}. Данные томографа GALILEOS сконвертированы в формат DICOM"

    def form_valid(self, form):
        form.instance.user = self.request.user
        #  Переименовываем название raw_archive в латиницу
        name = form.cleaned_data['raw_archive'].name
        dots = int(str(name).count('.'))
        name = unidecode(str(name).strip().lower().replace(' ', '_', dots - 1))
        form.instance.raw_archive.name = name
        return super().form_valid(form)
