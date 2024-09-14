from django import forms
from django_recaptcha.fields import ReCaptchaField


class ContactForm(forms.Form):
    name = forms.CharField(label='Имя', max_length=100)
    email = forms.EmailField(label='Email')
    message = forms.CharField(label='Сообщение', widget=forms.Textarea)
    confirm = ReCaptchaField()
