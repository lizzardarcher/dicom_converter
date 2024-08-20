from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render
from django.views.generic import CreateView

from apps.converter.forms import ResearchUploadForm
from apps.converter.models import Research


# Create your views here.
class UploadResearchView(SuccessMessageMixin, CreateView):
    model = Research
    form_class = ResearchUploadForm
    success_url = '/'
    template_name = 'create.html'
    success_message = 'Y YOYOYOYOYOY!'

    def form_valid(self, form):
        # self.object = form.save(commit=False)
        form.instance.user = self.request.user
        return super().form_valid(form)