# coding=utf8
import json
from django.core import serializers

# re-export function that was previously defined here for backward compatibility
from its_utils.app_model_to_dict import model_to_dict


def model_to_object(model, relations=None, excludes=None, fields=None, extras=None):
    # TODO проверить на тип

    """
    self.fields = None
    'fields':['name']
    self.excludes = None
    'excludes':['name']
    self.relations = None
    {'checkpoint': {}, 'projects':{'fields':['name']}}
    self.extras = None
    self.use_natural_keys = None
    """

    model = [model]
    str_ = serializers.serialize('wjson', model, indent=4,
                                 relations=relations,
                                 excludes=excludes,
                                 extras=extras,
                                 fields=fields)

    obj = json.loads(str_)[0]
