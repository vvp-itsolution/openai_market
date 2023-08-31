from PIL import Image
from django.http import HttpResponse
from django.utils.timezone import now

from its_utils.app_email.models import TemplatedOutgoingMail


def mark_tom(request, tom_id, tom_hash):
    TemplatedOutgoingMail.objects.filter(id=tom_id, hash=tom_hash, read__isnull=True).update(read=now())

    pixel = Image.new('RGBA', (1, 1), (255, 255, 255, 1))
    r = HttpResponse(content_type="image/png")
    pixel.save(r, 'PNG')

    return r
