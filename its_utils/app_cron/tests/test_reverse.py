from django.urls import reverse


def test_reverse(django_setup=False):
    if django_setup:
        import django
        django.setup()
    return reverse('admin:index')
