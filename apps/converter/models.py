from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


class Converter(models.Model):
    user = models.ManyToManyField(User, related_name='converters', blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    raw_archive=models.FileField(upload_to="converter/raw/",null=True,blank=True, validators=[FileExtensionValidator(['rar','zip'])], verbose_name='Архив от пользователя')
    is_anonymous=models.BooleanField(null=True,default=True, verbose_name='Анонимизировать данные')
    ready_archive = models.FileField(upload_to="converter/ready", null=True, blank=True, verbose_name="Архив с готовыми данными")
    slug = models.SlugField(unique=True, max_length=200, blank=True)

    def __str__(self):
        return str(self.user)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user + str(self.date_created))
        super(Converter, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Исследование'
        verbose_name_plural = 'Исследования'