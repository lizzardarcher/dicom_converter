from django import forms

from apps.converter.models import Research, TestResearch


class ResearchUploadForm(forms.ModelForm):
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
