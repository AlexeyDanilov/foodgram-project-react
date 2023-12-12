from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import F, Q, UniqueConstraint
from rest_framework.exceptions import ValidationError

MAX_VALUE = 150


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        'username',
        max_length=MAX_VALUE,
        unique=True,
        help_text=(
            "Required. 20 characters or fewer. Letters, "
            "digits and @/./+/-/_ only."
        ),
        validators=[
            username_validator,
        ],
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )
    first_name = models.CharField(
        "first name",
        max_length=MAX_VALUE,
    )
    last_name = models.CharField(
        'last name',
        max_length=MAX_VALUE,
    )
    email = models.EmailField(
        "email address", unique=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscribed_to = models.ForeignKey(
        User,
        verbose_name='На кого подписан',
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['subscriber', 'subscribed_to'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~Q(subscriber=F('subscribed_to')),
                name='subscriber_not_equal_subscribed_to'
            )
        ]

    def clean(self):
        super().clean()
        if self.subscriber == self.subscribed_to:
            raise ValidationError(
                'Подписчик не может подписаться на самого себя'
            )
