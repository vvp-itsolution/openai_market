from django.contrib import admin
from prettyjson import PrettyJSONWidget
from its_utils.functions.compatibility import get_json_field

JSONField = get_json_field()


class JsonAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }
