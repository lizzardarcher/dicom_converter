from time import sleep

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils.translation import activate
from django.views.generic import TemplateView, CreateView, FormView

from apps.admin_soft.utils import SuccessMessageMixin
from apps.home.forms import ContactForm


class PricesView(TemplateView):
    template_name = 'pages/info/prices.html'


class DetailedInfoView(TemplateView):
    template_name = 'pages/info/detailed_info.html'


class AboutView(TemplateView):
    template_name = 'pages/info/about.html'


class FAQView(TemplateView):
    template_name = 'pages/info/faq.html'


class HowItWorksView(TemplateView):
    template_name = 'pages/info/how_it_works.html'


class ContactView(SuccessMessageMixin, FormView):
    template_name = 'pages/info/contacts.html'
    form_class = ContactForm
    success_url = '/'
    success_message = 'Письмо отправлено успешно!'

    def form_valid(self, form):
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']

        send_mail(
            'Сообщение с сайта',  # Тема письма
            f'Имя: {name}\nEmail: {email}\n\nСообщение: {message}',  # Содержание письма
            settings.EMAIL_HOST_USER,  # От кого
            [settings.EMAIL_HOST_USER],  # Кому
        )

        return super().form_valid(form)


def set_lang_en(request):
    activate('en')
    return redirect('index')


def set_lang_ru(request):
    activate('ru')
    return redirect('index')
