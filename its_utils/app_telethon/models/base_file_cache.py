from django.db import models
from django.db.models import IntegerChoices
from telethon.tl.types import InputDocument, InputPhoto


class FileType(IntegerChoices):
    DOCUMENT = 0
    PHOTO = 1

    @staticmethod
    def from_type(cls):
        if cls == InputDocument:
            return FileType.DOCUMENT
        elif cls == InputPhoto:
            return FileType.PHOTO
        else:
            raise ValueError('The cls must be either InputDocument/InputPhoto')


class BaseFileCache(models.Model):
    """
    Для DjangoSession
    """

    session = models.ForeignKey('TelethonSession', on_delete=models.CASCADE)
    file_type = models.IntegerField(choices=FileType.choices)
    md5_digest = models.BinaryField()
    file_size = models.IntegerField()
    hash_value = models.BigIntegerField()
    file_id = models.IntegerField()

    class Meta:
        abstract = True
        unique_together = 'session', 'md5_digest', 'file_size', 'file_type',
