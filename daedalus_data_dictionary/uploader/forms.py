from django import forms
from django.db.models import Q
from django.conf import settings
from django.forms import formset_factory
from django.forms import BaseFormSet
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from dal.autocomplete import ModelSelect2
from django.core.urlresolvers import reverse_lazy

import csv
from aristotle_mdr.contrib.autocomplete import widgets
from daedalus_data_dictionary.uploader import utils 

class DataDictionaryUploader_Part1_NameAndUpload(forms.Form):
    name = forms.CharField(
        max_length=100,
        help_text=_('The name of the data dictionary')
    )
    data_dictionary = forms.FileField(help_text=_("Select a data dictionary CSV file to upload."))
    definition = forms.CharField(
        widget=forms.Textarea, required=False,
        help_text=_('Give a breif description of the data dictionary')
    )
    distribution = forms.BooleanField(
        label=_("We're going to override this"),
        required=False
    )
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(DataDictionaryUploader_Part1_NameAndUpload, self).__init__(*args, **kwargs)

        try:
            from aristotle_dse.models import Distribution
            self.fields['distribution'] = forms.ModelChoiceField(
                queryset=Distribution.objects.visible(self.user),
                required=False,
                empty_label="None",
                label=_("Data distribution"),
                help_text='To attach these records to a data distribution select it and the fields in the dictionary will be mapped to data elements',
                widget=widgets.ConceptAutocompleteSelect(
                    model=Distribution
                )
            )
        except:
            self.fields.pop('distribution')

class DynamicConceptAutocompleteSelect(ModelSelect2):
    def __init__(self, *args, **kwargs):
        qs_uuid = kwargs.pop('qs_uuid')
        self.model = kwargs.pop('model')
        kwargs.update(
            url=reverse_lazy(
                'upload-autocomplete',
                args=[self.model._meta.app_label, self.model._meta.model_name,qs_uuid]
            ),
            attrs={'data-html': 'true'}
        )
        super(DynamicConceptAutocompleteSelect, self).__init__(*args, **kwargs)


class DataDictionaryUploader_Part2_MatchingStuff(forms.Form):
    nope = forms.BooleanField(
        label=_("Skip this row"),
        help_text=_('Select to ignore his row when adding metadata from this dictionary.'),
        required=False
    )
    data_element = forms.BooleanField(
        label=_("We're going to override this"),
        required=False
    )
    object_class = forms.BooleanField(
        label=_("We're going to override this"),
        required=False
    )
    property = forms.BooleanField(
        label=_("We're going to override this"),
        required=False
    )
    data_type = forms.BooleanField(
        label=_("We're going to override this"),
        required=False
    )
    value_domain = forms.BooleanField(
        label=_("We're going to override this"),
        required=False
    )

    def __init__(self, *args, **kwargs):
        from aristotle_mdr import models

        self.row = kwargs.pop('row')
        self.user = kwargs.pop('user')
        super(DataDictionaryUploader_Part2_MatchingStuff, self).__init__(*args, **kwargs)
        
        de_qs = utils.data_dictionary_to_data_element_queryset(__user__=self.user, **self.row)
        oc_qs = utils.data_dictionary_to_object_class_queryset(__user__=self.user, **self.row)
        vd_qs = utils.data_dictionary_to_value_domain_queryset(__user__=self.user, **self.row)
        pr_qs = utils.data_dictionary_to_property_queryset(__user__=self.user, **self.row)
        dt_qs = utils.data_dictionary_to_datatype_queryset(__user__=self.user, **self.row)
        
        if de_qs:
            self.fields['data_element'] = forms.ModelChoiceField(
                queryset=de_qs,
                required=False,
                empty_label="None",
                label=_("Data element"),
                help_text='%s %s' % (self.row['name'], self.row['definition'][:50]),
                widget=DynamicConceptAutocompleteSelect(
                    qs_uuid=utils.register_queryset(de_qs),
                    model=models.DataElement
                ),
                initial=de_qs.first().pk if de_qs.first() else None
            )
        else:
            self.fields.pop('data_element')

        if oc_qs.exists():
            self.fields['object_class'] = forms.ModelChoiceField(
                queryset=oc_qs,
                required=False,
                empty_label="None",
                label=_("Object Class"),
                help_text=self.row['object_name'],
                widget=DynamicConceptAutocompleteSelect(
                    qs_uuid=utils.register_queryset(oc_qs),
                    model=models.ObjectClass
                ),
                initial=oc_qs.first().pk
            )
        else:
            self.fields.pop('object_class')

        if pr_qs.exists():
            self.fields['property'] = forms.ModelChoiceField(
                queryset=pr_qs,
                required=False,
                empty_label="None",
                label=_("Property"),
                help_text=self.row['property_name'],
                widget=DynamicConceptAutocompleteSelect(
                    qs_uuid=utils.register_queryset(pr_qs),
                    model=models.Property
                ),
                initial=pr_qs.first().pk
            )
        else:
            self.fields.pop('property')

        if dt_qs.exists():
            self.fields['data_type'] = forms.ModelChoiceField(
                queryset=dt_qs,
                required=False,
                empty_label="None",
                label=_("Data Type"),
                help_text=self.row['data_type'],
                widget=DynamicConceptAutocompleteSelect(
                    qs_uuid=utils.register_queryset(dt_qs),
                    model=models.DataType
                ),
                initial=dt_qs.first().pk
            )
        else:
            self.fields.pop('data_type')

        if vd_qs.exists():
            self.fields['value_domain'] = forms.ModelChoiceField(
                queryset=vd_qs,
                required=False,
                empty_label="None",
                label=_("Value Domain"),
                help_text=self.row['value_domain_description'][:50],
                widget=DynamicConceptAutocompleteSelect(
                    qs_uuid=utils.register_queryset(vd_qs),
                    model=models.ValueDomain
                ),
                initial=vd_qs.first().pk
            )
        else:
            self.fields.pop('value_domain')


class DataDictionaryUploader_Part2_MatchingStuffFormSet(BaseFormSet):
    form = DataDictionaryUploader_Part2_MatchingStuff
    extra = 0
    can_order = can_delete = False
    min_num = 0
    max_num = absolute_max = 1000
    validate_max = validate_min = False

    def __init__(self, *args, **kwargs):
        self.rows = kwargs.pop('rows')
        self.user = kwargs.pop('user')
        super(DataDictionaryUploader_Part2_MatchingStuffFormSet, self).__init__(*args, **kwargs)

    @cached_property
    def forms(self):
        """
        Instantiate forms at first property access.
        """
        # DoS protection is included in total_form_count()
        forms = []
        for i in range(self.total_form_count()):
            kwargs = {
                'row': self.rows[i],
                'user': self.user
            }
            forms.append(self._construct_form(i, **kwargs))
        return forms

    # def get_form_kwargs(self, index):
    #     1/0
    #     kwargs = super(DataDictionaryUploader_Part2_MatchingStuffFormSet, self).get_form_kwargs(index)
    #     kwargs['queryset'] = self.querysets[index]
    #     return kwargs


class DataDictionaryUploader_Part3_ConfirmStuff(forms.Form):
    name = forms.CharField()
    definition = forms.CharField(widget=forms.Textarea, required=False)
    object_name = forms.CharField(required=False)
    property_name = forms.CharField(required=False)
    value_domain_description = forms.CharField(widget=forms.Textarea, required=False)
    data_type = forms.CharField(required=False)
    maximum_length = forms.IntegerField(required=False)
    format_field = forms.CharField(widget=forms.Textarea, required=False)
    column = forms.CharField(required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)


    def __init__(self, *args, **kwargs):
        self.selected = kwargs.pop('selected')
        super(DataDictionaryUploader_Part3_ConfirmStuff, self).__init__(*args, **kwargs)

        if self.selected.get('nope'):
            # If they want to ignore this column, then everything can be ignored!
            self.nope = True
            self.fields.pop('name')
            self.fields.pop('definition')
            self.fields.pop('object_name')
            self.fields.pop('property_name')
            self.fields.pop('value_domain_description')
            self.fields.pop('data_type')
            self.fields.pop('maximum_length')
            self.fields.pop('format_field')
            self.fields.pop('column')
            self.fields.pop('notes')

        elif self.selected.get('data_element'):
            # If they have a match on the data element, then everything can be ignored!
            self.fields.pop('name')
            self.fields.pop('definition')
            self.fields.pop('notes')
            self.fields.pop('value_domain_description')
            self.fields.pop('maximum_length')
            self.fields.pop('format_field')
            self.fields.pop('data_type')
            self.fields.pop('object_name')
            self.fields.pop('property_name')
        else:
            if self.selected.get('value_domain'):
                self.fields.pop('value_domain_description')
                self.fields.pop('maximum_length')
                self.fields.pop('format_field')
            if self.selected.get('data_type'):
                self.fields.pop('data_type')
            if self.selected.get('object_class'):
                self.fields.pop('object_name')
            if self.selected.get('property'):
                self.fields.pop('property_name')


# DataDictionaryUploader_Part3_ConfirmStuffFormSet = formset_factory(
#     DataDictionaryUploader_Part3_ConfirmStuff,
#     extra=0,
# )

class DataDictionaryUploader_Part3_ConfirmStuffFormSet(BaseFormSet):
    form = DataDictionaryUploader_Part3_ConfirmStuff
    extra = 0
    can_order = can_delete = False
    min_num = 0
    max_num = absolute_max = 1000
    validate_max = validate_min = False

    def __init__(self, *args, **kwargs):
        self.selected = kwargs.pop('selected')
        self.user = kwargs.pop('user')
        super(DataDictionaryUploader_Part3_ConfirmStuffFormSet, self).__init__(*args, **kwargs)

    @cached_property
    def forms(self):
        """
        Instantiate forms at first property access.
        """
        # DoS protection is included in total_form_count()
        forms = []
        for i in range(self.total_form_count()):
            kwargs = {
                'selected': self.selected[i],
                # 'user': self.user,
            }
            forms.append(self._construct_form(i, **kwargs))
        return forms

    # def get_form_kwargs(self, index):
    #     kwargs = super(DataDictionaryUploader_Part3_ConfirmStuffFormSet, self).get_form_kwargs(index)
    #     kwargs['queryset'] = self.querysets[index]
    #     return kwargs


