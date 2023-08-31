# -*- coding: UTF-8 -*-


from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from its_utils.app_documentation.models import Image


@staff_member_required
def view_single_image(request):
    image = Image.objects.all()
    context = {'image': image}
    return render(request, 'documentation/single_image.html', context)
