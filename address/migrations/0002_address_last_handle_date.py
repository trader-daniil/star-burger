# Generated by Django 3.2.15 on 2023-02-27 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='last_handle_date',
            field=models.DateField(auto_now=True, verbose_name='Дата крайнего обращения к Геокодеру'),
        ),
    ]
