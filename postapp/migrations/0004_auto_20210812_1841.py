# Generated by Django 3.1.5 on 2021-08-12 09:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('postapp', '0003_auto_20210722_0924'),
    ]

    operations = [
        migrations.RenameField(
            model_name='favorites',
            old_name='tali_id',
            new_name='talk_id',
        ),
    ]
