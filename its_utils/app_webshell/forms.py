from django import forms
from .models import Script


class ScriptForm(forms.ModelForm):

    class Meta:
        model = Script
        fields = "__all__"

    class Media:
        css = {
            'all': (
                '/admin/webshell/static/css/codemirror.css',
                '/admin/webshell/static/css/highlight.min.css'
            )
        }
        js = (
            '/admin/webshell/static/js/codemirror.js',
            '/admin/webshell/static/js/python.js',
            '/admin/webshell/static/js/highlight.min.js',
        )