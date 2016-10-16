from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from model_utils import Choices

from aristotle_mdr.models import RichTextField
import aristotle_mdr as aristotle

class DataDictionary(aristotle.models.concept):
    """
    """
    template = "daedalus/storage/datadictionary.html"
    origin_file = models.FileField(
        help_text=_("If this data dictionary was part of a bulk upload, a copy of the file used to create it."),
        blank=True, null=True
    )
    included_concepts = models.ManyToManyField(
        aristotle.models._concept,
        related_name='dictionaries',
        through='DataDictionaryInclusion',
        blank=True, null=True
    )

class DataDictionaryInclusion(aristotle.models.aristotleComponent):

    @property
    def parentItem(self):
        return self.dictionary

    included_concept = models.ForeignKey(aristotle.models._concept, related_name='dictionary_inclusions')
    dictionary = models.ForeignKey(DataDictionary)
    context = models.TextField(
        null=True, blank=True,
        help_text=_("Additional context for the use of this concept within the data dictionary.")
    )
    # preferred_column_name = models.TextField(
    #     null=True, blank=True,
    #     help_text=_("Additional context for the use of this concept within the data dictionary.")
    # )
    # order = models.PositiveSmallIntegerField(
    #     "Position",
    #     null=True,
    #     blank=True,
    #     help_text=_("Position within a dictionary.")
    # )
    cascade = models.BooleanField(
        "Position",
        default=True,
        help_text=_(
            "If selected, this concept and all its components will be in the dictionary."
            "Otherwise only this concept will be in the dictionary.")
    )
