# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aristotle_mdr', '0015_concept_field_fixer_part3'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataDictionary',
            fields=[
                ('_concept_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='aristotle_mdr._concept')),
                ('origin_file', models.FileField(help_text='If this data dictionary was part of a bulk upload, a copy of the file used to create it.', upload_to=b'')),
            ],
            options={
                'abstract': False,
            },
            bases=('aristotle_mdr._concept',),
        ),
        migrations.CreateModel(
            name='DataDictionaryInclusion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('context', models.TextField(help_text='Additional context for the use of this concept within the data dictionary.', null=True, blank=True)),
                ('cascade', models.BooleanField(default=True, help_text='If selected, this concept and all its components will be in the dictionary.Otherwise only this concept will be in the dictionary.', verbose_name='Position')),
                ('dictionary', models.ForeignKey(to='storage.DataDictionary')),
                ('included_concept', models.ForeignKey(related_name='dictionary_inclusions', to='aristotle_mdr._concept')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='datadictionary',
            name='included_concepts',
            field=models.ManyToManyField(related_name='dictionaries', through='storage.DataDictionaryInclusion', to='aristotle_mdr._concept'),
        ),
    ]
