from django import forms
from django.core.validators import FileExtensionValidator
from pamo.constants import COLUMNS_SHOPI

OPCIONES = [(opcion, opcion) for opcion in COLUMNS_SHOPI]

class fileForm(forms.Form):
    file = forms.FileField( validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])], widget=forms.FileInput(attrs={'class': 'form-control form-control-sm file_upload'}))

class comparationForm(forms.Form):
    columns_shopi = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=OPCIONES,initial= 'N/A')