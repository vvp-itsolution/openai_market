from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from its_utils.app_get_params import get_params_from_sources


@user_passes_test(lambda u: u.is_superuser)
@get_params_from_sources
def authorize(request):
    user_id = request.its_params.get('user_id')
    user = get_object_or_404(User, id=user_id)
    login(request, user)
    return HttpResponse(u'You are logged in as {} now.'.format(user.username))
