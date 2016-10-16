# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datadictionary',
            name='included_concepts',
            field=models.ManyToManyField(related_name='dictionaries', null=True, through='storage.DataDictionaryInclusion', to='aristotle_mdr._concept', blank=True),
        ),
        migrations.AlterField(
            model_name='datadictionary',
            name='origin_file',
            field=models.FileField(help_text='If this data dictionary was part of a bulk upload, a copy of the file used to create it.', null=True, upload_to=b'', blank=True),
        ),
    ]
