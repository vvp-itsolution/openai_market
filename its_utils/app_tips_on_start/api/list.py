# -*- coding: utf-8 -*
from ..helpers import api_view
from ..models import Tip, TipCategory


@api_view
def tip_list(request, category_id=None):

    tips = Tip.objects.select_related('category').filter(active=True)
    if category_id is not None:
        category_id = int(category_id)
        if not TipCategory.objects.filter(id=category_id).exists():
            return 'Not Found', 404
        tips = tips.filter(category_id=category_id)

    if request.GET.get('shuffle') in ['true', '1']:
        tips = tips.order_by().order_by('?')

    return [tip.dict() for tip in tips]
