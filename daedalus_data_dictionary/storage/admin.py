from django.contrib import admin
import daedalus_data_dictionary.storage as storage

from aristotle_mdr.register import register_concept

class DataDictionaryInclusionInline(admin.TabularInline):
    model=storage.models.DataDictionaryInclusion
    extra=0
    raw_id_fields = ('included_concept',)
    # autocomplete_lookup_fields = {
    #     'fk': ['included_concept']
    # }
    fk_name = 'dictionary'


register_concept(storage.models.DataDictionary,
    extra_fieldsets=[
        ('Original file',
            {'fields': ['origin_file',
                        ]}
        ),
    ],
    extra_inlines=[DataDictionaryInclusionInline],
    reversion = {
        'follow': ['datadictionaryinclusion_set'],
        'follow_classes':[storage.models.DataDictionaryInclusion]
        },
    )
