import patoolib

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from pathlib import Path

from dicom_converter.settings import BASE_DIR


class Research(models.Model):
    user = models.ForeignKey(User, related_name='converters', blank=True, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    raw_archive=models.FileField(upload_to="converter/raw/",null=False,blank=False,
                            validators=[FileExtensionValidator(['rar','zip'])], verbose_name='Архив от пользователя')
    is_anonymous=models.BooleanField(null=True,default=True, verbose_name='Анонимизировать данные')
    ready_archive = models.FileField(upload_to="converter/ready", null=True, blank=True, verbose_name="Архив с готовыми данными")
    slug = models.SlugField(unique=True, max_length=200, blank=True)

    def __str__(self):
        return str(self.user) + ' ' +str(self.date_created)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.raw_archive.name}')
        print(str(BASE_DIR)+'/converter/raw/'+self.raw_archive.name)
        print(str(BASE_DIR)+'/extract_dir')
        patoolib.extract_archive(str(BASE_DIR)+'/converter/raw/'+self.raw_archive.name, BASE_DIR/'/extract_dir')
        super(Research, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Исследование'
        verbose_name_plural = 'Исследования'


