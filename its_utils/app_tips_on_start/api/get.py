# -*- coding: utf-8 -*
from ..helpers import api_view
from ..models import Tip


@api_view
def tip_get(request, tip_id):
    tip_id = int(tip_id)
    try:
        tip = Tip.objects.select_related('category').get(active=True, id=tip_id)
    except Tip.DoesNotExist:
        return 'Not Found', 404
    return tip.dict()
