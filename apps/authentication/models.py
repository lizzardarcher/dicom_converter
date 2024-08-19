# -*- encoding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


# class UserStatus(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     exp_date = models.DateField(default=now, null=True, blank=True, verbose_name='Оплачено по:')
#     is_vip = models.BooleanField(default=False, blank=True, verbose_name='VIP')
#     primary_color = models.CharField(max_length=100,
#                                      choices=[('primary', 'Розовый'), ('blue', 'Синий'), ('orange', 'Оранжевый'),
#                                               ('red', 'Красный'), ('green', 'Зеленый')],
#                                      default='Розовый', blank=True, verbose_name='Основной цвет')
#     main_theme = models.CharField(max_length=100, choices=[('white-content', 'Светлая'), ('', 'Темная')],
#                                   default='Темная',
#                                   blank=True, verbose_name='Тема Оформления')
#     tz = models.CharField(max_length=100, blank=True, default='Москва', choices=tz_choice, verbose_name='Город')
#
#     def __str__(self):
#         return self.user.username
#
#     class Meta:
#         verbose_name = 'Статус оплаты'
#         verbose_name_plural = 'Статус оплаты'

