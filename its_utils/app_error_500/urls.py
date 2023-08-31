from django.urls import path, include

print("Поменяйте в urls its_utils.app_error_500.urls на its_utils.app_error.urls")

urlpatterns = [
    path('', include('its_utils.app_error.urls')),
]