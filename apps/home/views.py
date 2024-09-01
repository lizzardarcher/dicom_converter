from time import sleep

from django.shortcuts import render
from django.views.generic import TemplateView, CreateView

from apps.home.forms import HomeForm
from apps.home.models import Home


class PricesView(TemplateView):
    template_name = 'pages/prices.html'

class DetailedInfoView(TemplateView):
    template_name = 'pages/detailed_info.html'

