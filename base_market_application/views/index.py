from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def index(request):


    return HttpResponse("f")
    return render(request, 'index.html', locals())
