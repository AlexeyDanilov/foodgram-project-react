from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    subscriptions = models.ManyToManyField(
        'users.User',
        related_name='subscribers',
        verbose_name='Подписки'
    )
