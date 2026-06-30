from django import forms
from django.utils.translation import pgettext_lazy
from django_recaptcha.fields import ReCaptchaField



class ContactForm(forms.Form):
    name = forms.CharField(label=pgettext_lazy('contacts', 'Имя'), max_length=100)
    email = forms.EmailField(label='Email')
    message = forms.CharField(label=pgettext_lazy('contacts', 'Сообщение'), widget=forms.Textarea)
    confirm = ReCaptchaField()
