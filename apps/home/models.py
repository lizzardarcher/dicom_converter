from django.contrib.auth.models import User
from django.db import models


class Log(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.CharField(max_length=50,
                             choices=(('Debug', 'Debug'), ('Info', 'Info'), ('Warning', 'Warning'), ('Error', 'Error')),
                             null=True, blank=True, verbose_name='Уровень')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    message = models.TextField(max_length=300, null=True, blank=True, verbose_name='Уведомление')

    def __str__(self):
        return f'{self.message} {self.user} {self.level} {self.created_at}'

    class Meta:
        verbose_name = 'Лог'
        verbose_name_plural = 'Логи'