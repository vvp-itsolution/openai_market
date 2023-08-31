from django.forms import ModelChoiceField
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
ModelChoiceField.widget = ForeignKeyRawIdWidget