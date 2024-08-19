from time import sleep

from django.shortcuts import render
from django.views.generic import TemplateView, CreateView

from apps.home.forms import HomeForm
from apps.home.models import Home


class HomeView(TemplateView):
    template_name = 'index.html'

class HomeCreateView(CreateView):
    model = Home
    form_class = HomeForm
    template_name = 'create.html'
    success_url = '/'

    def form_valid(self, form):
        sleep(5)
        return super().form_valid(form)