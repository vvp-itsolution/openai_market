# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from bitrix_utils.bitrix_auth.functions.bitrix_user_required import bitrix_user_required

from bitrix_utils.bitrix_auth.models import BitrixAccessObject, BitrixAccessObjectSet
from its_utils.app_get_params import get_params_from_sources


@csrf_exempt
@get_params_from_sources
@bitrix_user_required
def access_object_set_save(request):

    """
    Перезаписать все объекты для данного правила
    """

    if not request.its_params.items():
        return HttpResponse('Need objects ids', status=400)

    set_id = request.its_params.get('id')

    if set_id:
        try:
            BitrixAccessObjectSet.objects.get(id=set_id)
            BitrixAccessObject.objects.filter(set_id=set_id).delete()
        except BitrixAccessObjectSet.DoesNotExist:
            return HttpResponse('Bad id', status=400)
    else:
        set_id = BitrixAccessObjectSet.objects.create().id

    objects = []
    for type_, ids in request.its_params.items():
        for id_ in ids:
            objects.append(BitrixAccessObject(type=type_, type_id=id_, set_id=set_id))

    BitrixAccessObject.objects.bulk_create(objects)

    return HttpResponse()
