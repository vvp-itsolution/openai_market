# -*- coding: utf-8 -*-
from itertools import chain
import django
from django.db.models.fields.related import OneToOneRel, ManyToOneRel, ManyToManyRel, ForeignKey, ManyToManyField


def model_to_dict_django1(instance, fields=None, exclude=None, relations=None, extras=None):
    """Helper for serializing orm-instances to dictionaries.
    Originally intended to use with Django Forms (as ``initial`` keyword argument).
    Another possible usage for this helper is easy serialization of
    model instances to dictionaries those can be used arbitrarily.

    Usage example:
    We have a Product with many fields. We want to serialize it to json,
    but we want to exclude `ordering` and `sap_code` fields of product.
    We also need to add a dict required to render sizes table on the client,
    so we pass extras=['sizes_table'] so that product.sizes_table() will
    be added to result.
    Furthermore we want to add to result category name of product
    and featured products in the category. That's how we would do it:
    ```
    def my_api_view_get_product(request):
        product = get_object_or_404(Product, pk=1)
        product_as_dict = model_to_dict(
            Product,
            exclude=['ordering', 'sap_code'],
            extras=['sizes_table'],
            relations=dict(
                category=dict(
                    fields=['id', 'name'],
                    relations=dict(
                        featured_products=dict(
                            # for featured products we need only few fields
                            # enough to render a card with link to product.
                            # So it's better to provide them as ``fields``
                            # rather than write dozen of fields for ``exclude``.
                            fields=[
                                'id',
                                'name',
                                'short_description',
                                'preview_picture',
                            ],
                        ),
                    ),
                ),
            ),
        )
        return JsonResponse(product_as_dict)

    response will contain json:

        {
            "id": 1,
            "name": "Платье в горошек",,
            "preview_picture": "/media/pic2.jpg"
            "sizes_table": {"xs": {...}, "s": {...}, ...}
            ... many more fields,
            "category": {"id": 42,
                         "name": "Платья",
                         "featured_products": [
                             {"id": 2,
                              "name": "Шапочка",
                              "short_description": "...",
                              "preview_picture": "/media/pic2.jpg"},
                             ...
                         ]}
        }
    ```

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.

    ``relations`` is an optional `dict` where keys are names of relationship fields
    and values are dictionaries with optional fields: `fields`, `exclude`, `relations`, `extras`.
    They'll as kwargs for recursive calls of model_to_dict(instance, **kwargs) for every
    related instance. Supports both to-many and to-one kinds of relationships.

    ``extras`` is an optional list of method names. Each method will be called without arguments
    and its return value will be added to resulting dict.

    Returns a dict populated from ``instance`` and its relationships.

    NB! Silently ignores invalid fields and excludes.
    You should inspect result to contain all the fields that you expect.
    """
    # avoid a circular import

    if not relations:
        relations = {}

    opts = instance._meta
    data = {}

    for f in chain(opts.concrete_fields, opts.virtual_fields, opts.many_to_many, opts.related_objects):
        # iterating over all the fields of model
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, ManyToManyField):
            # If the object doesn't have a primary key yet, just use an empty
            # list for its m2m fields. Calling f.value_from_object will raise
            # an exception.
            if instance.pk is None:
                data[f.name] = []
            else:
                # MultipleChoiceWidget needs a list of pks, not object instances.
                qs = f.value_from_object(instance)
                if relations.get(f.name) is not None:
                    data[f.name] = [model_to_dict_django1(item, **relations.get(f.name)) for item in qs]
                else:
                    if qs._result_cache is not None:
                        data[f.name] = [item.pk for item in qs]
                    else:
                        data[f.name] = list(qs.values_list('pk', flat=True))
        elif isinstance(f, OneToOneRel):  # НУЖНОЛИ ЭТО?
            if relations.get(f.name) is not None:
                if hasattr(instance, f.name):
                    data[f.name] = model_to_dict_django1(getattr(instance, f.name), **relations.get(f.name))
                else:
                    data[f.name] = None
        elif isinstance(f, ManyToManyRel):  # НУЖНОЛИ ЭТО?
            pass
        elif isinstance(f, ManyToOneRel):
            if relations.get(f.name) is not None:
                data[f.name] = [model_to_dict_django1(item, **relations.get(f.name)) for item in
                                getattr(instance, f.name).all()]
        elif isinstance(f, ForeignKey):
            if relations.get(f.name) is not None:
                subinstance = getattr(instance, f.name)
                if subinstance:
                    data[f.name] = model_to_dict_django1(subinstance, **relations.get(f.name))
                else:
                    data[f.name] = None
            else:
                data["%s_id" % f.name] = f.value_from_object(instance)
        else:
            data[f.name] = f.value_from_object(instance)

    if extras:
        for extra in extras:
            data[extra] = getattr(instance, extra)()

    return data


def model_to_dict_django2(instance, fields=None, exclude=None, relations=None, extras=None):
    """
    Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    # в тикет-сервере очень многое завязано на django-1.x версию данной функции,
    # todo: дотестировать что работает как ожидается

    relations = relations or {}
    opts = instance._meta
    data = {}
    for f in opts.get_fields():
        #print(f)
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue

        if isinstance(f, ManyToManyRel):
            f = f.field

        if isinstance(f, ManyToManyField):
            # If the object doesn't have a primary key yet, just use an empty
            # list for its m2m fields. Calling f.value_from_object will raise
            # an exception.
            if instance.pk is None:
                data[f.name] = []

            elif hasattr(instance, f.name):
                # MultipleChoiceWidget needs a list of pks, not object instances.
                qs = f.value_from_object(instance)
                if relations.get(f.name) is not None:
                    data[f.name] = [model_to_dict_django1(item, **relations.get(f.name)) for item in qs]
                else:
                    if isinstance(qs, list):
                        data[f.name] = [item.pk for item in qs]
                    else:
                        data[f.name] = list(qs.values_list('pk', flat=True))

        elif isinstance(f, OneToOneRel): #НУЖНОЛИ ЭТО?
            if relations.get(f.name, None) is not None:
                if hasattr(instance, f.name):
                    data[f.name] = model_to_dict_django2(getattr(instance, f.name), **relations.get(f.name))
                else:
                    data[f.name] = None
        elif isinstance(f, ManyToOneRel):
            if relations.get(f.name, None) is not None:
                data[f.name] = [model_to_dict_django2(item, **relations.get(f.name)) for item in getattr(instance, f.name).all()]
        elif isinstance(f, ForeignKey):
            if relations.get(f.name, None) is not None:
                subinstance = getattr(instance, f.name)
                if subinstance:
                    data[f.name] = model_to_dict_django2(subinstance, **relations.get(f.name))
                else:
                    data[f.name] = None
            else:
                data["%s_id" % f.name] = f.value_from_object(instance)
        else:
            data[f.name] = f.value_from_object(instance)

        if extras:
            for extra in extras:
                data[extra] = getattr(instance, extra)()

    return data


model_to_dict = model_to_dict_django1 if django.VERSION[0] == 1 \
    else model_to_dict_django2
