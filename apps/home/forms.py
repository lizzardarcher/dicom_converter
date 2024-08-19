from django import forms

from apps.home.models import Home


class HomeForm(forms.ModelForm):
    class Meta:
        model = Home
        fields = ['name']
