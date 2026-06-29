from django import forms
from django.core.exceptions import ValidationError

from apps.converter.models import Research, TestResearch, UserSettings

class ResearchUploadForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            user_settings = UserSettings.objects.filter(user=self.user).last()
            avail = user_settings.research_avail_count if user_settings else 0
            if not avail:
                raise ValidationError(
                    'Недостаточно доступных конвертаций. Пополните баланс, чтобы загрузить исследование.'
                )
        return cleaned_data

    class Meta:
        model = Research
        fields = ['raw_archive', 'is_anonymous', 'is_one_file']
        widgets = {

            'raw_archive': forms.FileInput(attrs={'accept': '.rar, .zip, .7z'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'flexSwitchCheckDefault1'}),
            'is_one_file': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'flexSwitchCheckDefault2',}),
        }


class TestResearchUploadForm(forms.ModelForm):
    class Meta:
        model = TestResearch
        fields = ['raw_archive']
