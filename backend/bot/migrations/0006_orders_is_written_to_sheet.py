# Generated by Django 4.2.6 on 2024-01-06 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='is_written_to_sheet',
            field=models.BooleanField(default=False),
        ),
    ]