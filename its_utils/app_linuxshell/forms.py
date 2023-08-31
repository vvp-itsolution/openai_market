from django import forms
from .models import Script


class ScriptForm(forms.ModelForm):

    class Meta:
        model = Script
        fields = "__all__"

    class Media:
        css = {
            'all': (
                '/admin/linuxshell/static/css/codemirror.css',
                '/admin/linuxshell/static/css/highlight.min.css'
            )
        }
        js = (
            '/admin/linuxshell/static/js/codemirror.js',
            '/admin/linuxshell/static/js/python.js',
            '/admin/linuxshell/static/js/highlight.min.js',
        )