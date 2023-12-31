# Generated by Django 4.2.6 on 2023-11-04 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_alter_orders_client_products_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='latitude',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orders',
            name='longitude',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='chats',
            name='type',
            field=models.CharField(choices=[('channel', 'Kanal'), ('tashkent_channel', 'Toshkent uchun kanal'), ('regions_channel', 'Viloyatlar uchun kanal')], max_length=100),
        ),
    ]
