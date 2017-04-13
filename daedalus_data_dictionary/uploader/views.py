import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from formtools.wizard.views import SessionWizardView
import csv

from daedalus_data_dictionary.uploader.utils import get_queryset_from_uuid

from daedalus_data_dictionary.uploader.forms import (
    DataDictionaryUploader_Part1_NameAndUpload,
    DataDictionaryUploader_Part2_MatchingStuffFormSet,
    DataDictionaryUploader_Part3_ConfirmStuffFormSet
)

class DataDictionaryUploader(SessionWizardView):
    form_list = [
        DataDictionaryUploader_Part1_NameAndUpload,
        DataDictionaryUploader_Part2_MatchingStuffFormSet,
        DataDictionaryUploader_Part3_ConfirmStuffFormSet
    ]
    template_list = [
        "daedalus/uploader/wizard/1_upload.html",
        "daedalus/uploader/wizard/2_matcher.html",
        "daedalus/uploader/wizard/3_confirm.html"
    ]
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'data_dictionaries'))
    template_name = "daedalus/uploader/wizard/1_upload.html"

    fieldnames = [
        'name',
        'definition',
        'object_name',
        'property_name',
        'value_domain_description',
        'data_type',
        'maximum_length',
        'format_field',
        'column',
        'notes',
    ]

    def get_dict_from_file(self):
        upload = self.storage.get_step_files('0')['0-data_dictionary'] #.read()

        reader = csv.DictReader(upload, fieldnames=self.fieldnames)
        reader = [
            row for row in list(reader)
            # The row is all blank, ignore it
            if not all(map(lambda y: y is None or y.strip() == "", row.values()))
        ]

        # Skip header (its mandatory)
        return reader[1:]

    def get_template_names(self):
        return [self.template_list[int(self.steps.current)]]

    def get_form_kwargs(self, step):
        kwargs = super(DataDictionaryUploader, self).get_form_kwargs(step)
        if int(step) == 1:
            help_texts = []
            rows = []
            for row in self.get_dict_from_file():
                help_texts.append(row['name'])
                rows.append(row)
            kwargs.update({'rows':rows})
            kwargs.update({'step':step})
        elif int(step) == 2:
            kwargs.update({
                'selected':self.get_cleaned_data_for_step('1'),
                # 'user':self.request.user
            })
        kwargs.update({'user':self.request.user})
        return kwargs

    def get_form_initial(self, step, **kwargs):
        initial = super(DataDictionaryUploader, self).get_form_initial(step)

        if int(step) == 0:
            initial = {}
            if 'distribution' in self.request.GET.keys():
                initial = {
                    'distribution': self.request.GET.get('distribution')
                }
        if int(step) == 1:
            initial = []
            for row in self.get_dict_from_file():
                initial.append({'nope': False})
        elif int(step) == 2:
            initial = []
            for row in self.get_dict_from_file():
                initial.append(row)
        return initial

    #@transaction.atomic
    def done(self, form_list, **kwargs):
        # Objects that were created during the wizard
        details = {
            'data_dictionary':{},
            'object_classes':[],
            'properties':[],
            'data_types':[],
            'data_elements':[],
            'data_element_concepts':[],
        }
        # Now, lets save everything!

        if 'daedalus_data_dictionary.storage' in settings.INSTALLED_APPS:
            from daedalus_data_dictionary.storage import models as DDM
            dd = DDM.DataDictionary.objects.create(
                name = self.get_cleaned_data_for_step('0')['name'],
                definition = self.get_cleaned_data_for_step('0')['definition'],
                origin_file = self.storage.get_step_files('0')['0-data_dictionary'],
                submitter=self.request.user
            )
            details['data_dictionary'] = dd
        else:
            details['data_dictionary'] = {
                'name': self.get_cleaned_data_for_step('0')['name'],
                'definition': self.get_cleaned_data_for_step('0')['definition'],
            }

        # names that were used to create objects
        names = {
            'object_classes':{},
            'properties':{},
            'data_types':{},
            'data_elements':{},
            'data_element_concepts':{},
        }

        from aristotle_mdr import models
        for elems, values in zip(self.get_cleaned_data_for_step('1'),self.get_cleaned_data_for_step('2')):
            if elems.get('nope', False):
                # Skip rows when instructed
                continue

            if values.get('object_name', None):
                if values['object_name'] not in names['object_classes'].keys():
                    oc = models.ObjectClass.objects.create(
                        name=values['object_name'],
                        definition='',
                        submitter=self.request.user
                    )
                    details['object_classes'].append(oc)
                    names['object_classes'][values['object_name']] = oc
                else:
                    oc = names['object_classes'][values['object_name']]
            else:
                oc = elems.get('object_class', None)

            if values.get('property_name', None):
                if values['property_name'] not in names['properties'].keys():
                    pr = models.Property.objects.create(
                        name=values['property_name'],
                        definition='',
                        submitter=self.request.user
                    )
                    details['properties'].append(pr)
                    names['properties'][values['property_name']] = pr
                else:
                    pr = names['properties'][values['property_name']]
            else:
                pr = elems.get('property', None)

            if values.get('data_type', None):
                if values['data_type'] not in names['data_types'].keys():
                    dt = models.DataType.objects.create(
                        name=values['data_type'],
                        definition='',
                        submitter=self.request.user
                    )
                    details['data_types'].append(dt)
                    names['data_types'][values['data_type']] = dt
                else:
                    dt = names['data_types'][values['data_type']]
            else:
                dt = elems.get('data_type', None)

            if any(values.get(val, None) for val in [
                'value_domain_description', 'maximum_length', 'format_field'
            ]):
                if elems.get('data_element', None):
                    postfix = elems.get('data_element').name
                elif 'name' in values.keys():
                    postfix = values.get('name')
                else:
                    # Don't think we will ever get here, but just in case
                    postfix = 'uploaded data element in data dictionary'
                vd_name = 'Value domain for %s' % postfix

                vd = models.ValueDomain(
                    name=vd_name,
                    definition='',
                    description=values.get('value_domain_description',""),
                    maximum_length=values.get('maximum_length',""),
                    format=values.get('format_field',""),
                    submitter=self.request.user
                )
                vd.data_type = dt
                vd.save()
            else:
                vd = elems.get('value_domain', None)

            if not elems.get('data_element', None):
                if values['name'] not in names['data_elements'].keys():
                    # if oc or pr:
                    #     pass
                    dec_name = '%s-%s' % (oc.name, pr.name)
                    dec = models.DataElementConcept(
                        name=dec_name,
                        definition='',
                    )
                    dec.objectClass = oc
                    dec.property = pr
                    dec.save()
                    details['data_element_concepts'].append(dec)

                    if values['name']:
                        de_name = values['name']
                    elif dt:
                        de_name = '%s-%s, %s' % (oc.name, pr.name, dt.name)
                    else:
                        de_name = '%s-%s' % (oc.name, pr.name)
                    de = models.DataElement(
                        name=de_name,
                        short_name=values['name'],
                        definition='',
                        submitter=self.request.user
                    )
                    de.dataElementConcept = dec
                    de.valueDomain = vd
                    de.save()
                    details['data_elements'].append(de)
                    names['data_elements'][values['name']] = de
                else:
                    de = names['data_elements'][values['name']]
            else:
                de = elems['data_element']

            if 'daedalus_data_dictionary.storage' in settings.INSTALLED_APPS:
                di = DDM.DataDictionaryInclusion.objects.create(
                    dictionary=dd,
                    included_concept=de,
                    context="Column name: %s"%values['column'],
                    # preferred_column_name=values['column']
                )
            if 'distribution' in self.get_cleaned_data_for_step('0').keys():
                try:
                    from aristotle_dse.models import DistributionDataElementPath
                    ddep = DistributionDataElementPath.objects.create(
                        distribution=self.get_cleaned_data_for_step('0')['distribution'],
                        data_element=de,
                        logical_path=values['column'],
                    )
                except ImportError:
                    pass

        return render(self.request, 'daedalus/uploader/wizard/4_done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'saved_details':details
        })

    def get_context_data(self, form, **kwargs):
        context = super(DataDictionaryUploader, self).get_context_data(form=form, **kwargs)

        if int(self.steps.current) == 2:
            context.update({'selected': self.get_cleaned_data_for_step('1')})

        if int(self.steps.current) > 0:
            upload = self.storage.get_step_files('0')['0-data_dictionary'] #.read()
            reader = list(csv.reader(upload)) #, fieldnames=self.fieldnames))
            header = reader[0]
            rows = [
                row for row in reader
                # The row is not blank, yield it
                if not all(map(lambda y: y.strip() == "", row))
            ][1:]
            context.update({
                'header': header,
                'rows': rows
            })


        context.update({
            'percent_complete': 100*int(self.steps.step0) / int(self.steps.count),

        })

        return context

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super(DataDictionaryUploader, self).dispatch(request, *args, **kwargs)

from aristotle_mdr.contrib.autocomplete.views import GenericAutocomplete
class DDConceptAutocomplete(GenericAutocomplete):
    template_name = "autocomplete_light/concept.html"

    def get_queryset(self):
        from django.apps import apps
        qs_uuid = self.kwargs.get('qs_uuid', None)
        model = apps.get_model(self.kwargs.get('app_label'), self.kwargs.get('model_name'))

        qs = get_queryset_from_uuid(qs_uuid, model).visible(self.request.user)

        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs
