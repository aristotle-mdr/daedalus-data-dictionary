import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.shortcuts import redirect, render, get_object_or_404
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

    def get_template_names(self):
        return [self.template_list[int(self.steps.current)]]

    def get_form_kwargs(self, step):
        kwargs = super(DataDictionaryUploader, self).get_form_kwargs(step)
        if int(step) == 1:
            upload = self.storage.get_step_files('0')['0-data_dictionary'] #.read()
            fieldnames = [
                'name',
                'definition',
                'object_name',
                'property_name',
                'value_domain_description',
                'datatype',
                'maximum_length',
                'format_field',
                'column',
                'notes',
            ]
            reader = csv.DictReader(upload, fieldnames=fieldnames)
            querysets = []
            help_texts = []
            rows = []
            for row in reader:
                help_texts.append(row['name'])
                rows.append(row)
            kwargs.update({'rows':rows, 'user':self.request.user})
        elif int(step) == 2:
            kwargs.update({
                'selected':self.get_cleaned_data_for_step('1'),
                # 'user':self.request.user
            })
        return kwargs

    def get_form_initial(self, step, **kwargs):
        initial = super(DataDictionaryUploader, self).get_form_initial(step)

        fieldnames = [
            'name',
            'definition',
            'object_name',
            'property_name',
            'value_domain_description',
            'datatype',
            'maximum_length',
            'format_field',
            'column',
            'notes',
        ]

        if int(step) == 1:
            upload = self.storage.get_step_files('0')['0-data_dictionary'] #.read()
            reader = csv.DictReader(upload, fieldnames=fieldnames)
            initial = []
            next(reader)  # Skip header (its mandatory)
            for row in reader:
                initial.append({'nope': False})
        elif int(step) == 2:
            # num_of_dates =  self.get_cleaned_data_for_step(str(int(step) - 1))['date'].split(',')
            # form_class.extra = len(num_of_dates)-1
            upload = self.storage.get_step_files('0')['0-data_dictionary'] #.read()
            reader = csv.DictReader(upload, fieldnames=fieldnames)
            initial = []
            next(reader)  # Skip header (its mandatory)
            for row in reader:
                print row
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
        #Save everything!
        details['data_dictionary']['name'] = self.get_cleaned_data_for_step('0')['name']
        details['data_dictionary']['definition'] = self.get_cleaned_data_for_step('0')['definition']
        
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
            print 'elems=',elems
            print 'values=',values
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
                vd_name = "Value domain for %s"
                if elems.get('data_element', None):
                    postfix = elems.get('data_element').name
                elif 'data_element' in values.keys():
                    postfix = values.get('data_element')
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
                    
                    de = models.DataElement(
                        name=values['object_name'],
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


        return render(self.request, 'daedalus/uploader/wizard/4_done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'saved_details':details
        })

    def get_context_data(self, form, **kwargs):
        context = super(DataDictionaryUploader, self).get_context_data(form=form, **kwargs)

        if int(self.steps.current) == 2:
            context.update({'selected': self.get_cleaned_data_for_step('1')})
        
        context.update({
            'percent_complete': 100*int(self.steps.step0) / int(self.steps.count)
        })
        
        return context

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
        return qs
