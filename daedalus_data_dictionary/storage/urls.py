from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _
from aristotle_mdr.contrib.generic.views import GenericAlterOneToManyView, generic_foreign_key_factory_view

from daedalus_data_dictionary.storage import models

urlpatterns = [
    url(r'^dictionary/(?P<iid>\d+)?/edit/?$',
        GenericAlterOneToManyView.as_view(
            model_base=models.DataDictionary,
            model_to_add=models.DataDictionaryInclusion,
            model_base_field='datadictionaryinclusion_set',
            model_to_add_field='dictionary',
            #ordering_field='order',
            form_add_another_text=_('Add a metadata concept'),
            form_title=_('Change dictionary concept entries')
        ), name='data_dictionary_edit'),
]
