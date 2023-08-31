from django.template.response import TemplateResponse

def error_500_info(request):
    return TemplateResponse(request, 'app_error_500/error_500_info.html', status=500)
