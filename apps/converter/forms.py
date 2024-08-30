from django import forms

from apps.converter.models import Research


class ResearchUploadForm(forms.ModelForm):
    class Meta:
        model = Research
        fields = ['raw_archive', 'is_anonymous']
        widgets = {
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'flexSwitchCheckDefault'}),
        }
