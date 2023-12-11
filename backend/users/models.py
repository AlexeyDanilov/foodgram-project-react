from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

MIN_VALUE = 2
MAX_VALUE = 50


class User(AbstractUser):
    subs = models.ManyToManyField(
        'users.User',
        verbose_name='Подписки',
        through='Subscription'
    )
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=MAX_VALUE,
        unique=True,
        help_text=_(
            "Required. 20 characters or fewer. Letters, "
            "digits and @/./+/-/_ only."
        ),
        validators=[
            username_validator,
            MinLengthValidator(limit_value=5),
            MaxLengthValidator(limit_value=MAX_VALUE)
        ],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
        null=False, blank=False
    )
    first_name = models.CharField(
        _("first name"),
        max_length=MAX_VALUE,
        blank=False,
        null=True,
        validators=[
            MinLengthValidator(limit_value=MIN_VALUE),
            MaxLengthValidator(limit_value=MAX_VALUE)
        ]
    )
    last_name = models.CharField(
        _("last name"),
        max_length=MAX_VALUE,
        blank=False,
        null=True,
        validators=[
            MinLengthValidator(limit_value=MIN_VALUE),
            MaxLengthValidator(limit_value=MAX_VALUE)
        ]
    )
    email = models.EmailField(
        _("email address"), blank=False, null=False, unique=True
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
                name='unique_subscriзtion'
            )
        ]

    def clean(self):
        if self.subscriber == self.subscribed_to:
            raise ValidationError(
                'Подписчик не может подписаться на самого себя'
            )
