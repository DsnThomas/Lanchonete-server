# Generated by Django 5.2.1 on 2025-06-14 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0007_supplier_cnpj_cpf'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Cidade'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='neighborhood',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Bairro'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='number',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Número'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='street',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Rua'),
        ),
    ]
