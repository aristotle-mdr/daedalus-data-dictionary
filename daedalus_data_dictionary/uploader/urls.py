from django.conf.urls import url
from daedalus_data_dictionary.uploader import views

urlpatterns = [
    url(
        r'^upload/ac/(?P<app_label>[a-z_]+)-(?P<model_name>[a-z_]+)/(?P<qs_uuid>.*)/',
        views.DDConceptAutocomplete.as_view(),
        name='upload-autocomplete',
    ),
    url(r'^upload', views.DataDictionaryUploader.as_view()),
]
