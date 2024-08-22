from django.template import context
from unidecode import unidecode

from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render
from django.views.generic import CreateView, ListView

from apps.converter.forms import ResearchUploadForm
from apps.converter.models import Research


# Create your views here.
class UploadResearchView(SuccessMessageMixin, CreateView):
    model = Research
    form_class = ResearchUploadForm
    success_url = '/'
    template_name = 'create.html'
    success_message = 'SUCCESS!'

    def get_context_data(self, **kwargs):
        context = super(UploadResearchView, self).get_context_data(**kwargs)
        context.update({
            'research': Research.objects.all(),
        })
        return context

    def get_success_message(self, cleaned_data):
        return f"{self.success_message} {cleaned_data['raw_archive'].name}"

    def form_valid(self, form):
        form.instance.user = self.request.user
        #  Переименовываем название raw_archive в латиницу
        name = form.cleaned_data['raw_archive'].name
        dots = int(str(name).count('.'))
        name = unidecode(str(name).strip().lower().replace(' ', '_', dots - 1))
        form.instance.raw_archive.name = name
        return super().form_valid(form)
