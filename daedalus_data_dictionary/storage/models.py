from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from model_utils import Choices

from aristotle_mdr.models import RichTextField
import aristotle_mdr as aristotle

class RegisteredDataSet(aristotle.models.concept):
    """
    A registered dataset
    """
    template = "magda_data_registry/registereddataset.html"
#    name = models.CharField(max_length=256, null=False, blank=False)  # shortname
#    title = models.CharField(max_length=256, null=False, blank=False)  # name
    jurisdiction = models.TextField()
    license_title = models.TextField()
    spatial_coverage = models.TextField()
    author = models.TextField()
    temporal_coverage_from = models.CharField(max_length=256, blank=True)
    notes = models.TextField()
    data_state = models.CharField(max_length=256, blank=True)
    where_to_get = models.TextField()
    # owner = models.ForeignKey(
    #     Organisation,  # RegistrationAuthority
    # )
    language = models.CharField(max_length=256, blank=True)

    @property
    def registry_cascade_items(self):
        from aristotle_mdr import models
        return list(self.resources.all())+list(
            models.DataElement.objects.filter(columns__dataset=self)
        )+list(
            models.ValueDomain.objects.filter(dataelement__columns__dataset=self)
        )

class DataSetResource(aristotle.models.concept):
    # name = models.CharField(max_length=256, blank=True)
    # description = models.TextField()
    template = "magda_data_registry/dataresource.html"
    url = models.TextField()
    position = models.PositiveIntegerField()
    filetype = models.CharField(max_length=256, blank=True)

    dataset = models.ForeignKey(
        RegisteredDataSet,
        related_name="resources"
    )
    data_elements = models.ManyToManyField(
        aristotle.models.DataElement,
        related_name='columns',
        through='DataSetResourceColumn'
    )

class DataSetResourceColumn(aristotle.models.aristotleComponent):
    class Meta:
        ordering = ['order']

    @property
    def parentItem(self):
        return self.resource

    data_element = models.ForeignKey(aristotle.models.DataElement)
    resource = models.ForeignKey(DataSetResource)
    column_name = models.CharField(
        max_length=256,
        help_text=_("The name of this data element as a column in the dataset.")
        )
    order = models.PositiveSmallIntegerField(
        "Position",
        null=True,
        blank=True,
        help_text=_("Column position within a dataset.")
        )
