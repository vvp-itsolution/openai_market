from django.urls import path

from .views.view_error_403 import view_error_403
from .views.view_error_500 import view_error_500

urlpatterns = [
    path('500/', view_error_500, name='error500'),
    path('403/', view_error_403, name='error403'),
]