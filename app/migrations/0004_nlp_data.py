# Generated by Django 3.2.5 on 2023-12-11 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20231114_1836'),
    ]

    operations = [
        migrations.CreateModel(
            name='NLP_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('data', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
