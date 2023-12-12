# Generated by Django 3.2.3 on 2023-12-12 07:07

import django.contrib.auth.validators
import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20231211_0044'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='subscription',
            name='unique_subscriзtion',
        ),
        migrations.RemoveField(
            model_name='user',
            name='subs',
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=150, null=True, verbose_name='first name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=150, null=True, verbose_name='last name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 20 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.UniqueConstraint(fields=('subscriber', 'subscribed_to'), name='unique_subscription'),
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.CheckConstraint(check=models.Q(('subscriber', django.db.models.expressions.F('subscribed_to')), _negated=True), name='subscriber_not_equal_subscribed_to'),
        ),
    ]
