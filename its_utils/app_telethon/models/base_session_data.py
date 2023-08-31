from typing import Optional

from django.contrib import admin
from django.db import models
from telethon.tl.types.updates import State


class BaseSessionData(models.Model):
    """
    Для DjangoSession
    """

    session = models.OneToOneField('TelethonSession', primary_key=True, on_delete=models.CASCADE)

    # data
    auth_key = models.BinaryField(null=True, blank=True)
    dc_id = models.IntegerField(default=0, db_index=True)
    port = models.IntegerField(null=True, blank=True)
    server_address = models.CharField(max_length=255, null=True, blank=True)
    takeout_id = models.BigIntegerField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    # state
    state_saved = models.BooleanField(default=False)
    state_pts = models.IntegerField(null=True, blank=True)
    state_qts = models.IntegerField(null=True, blank=True)
    state_date = models.DateTimeField(null=True, blank=True)
    state_seq = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True

    class Admin(admin.ModelAdmin):
        raw_id_fields = 'session',

    def __str__(self):
        return str(self.session)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.auth_key, memoryview):
            self.auth_key = self.auth_key.tobytes()

    @property
    def entity_model(self):
        return self.session.ENTITY_MODEL

    @property
    def file_cache_model(self):
        return self.session.FILE_CACHE_MODEL

    @property
    def entities(self):
        return self.entity_model.objects.filter(session=self.session)

    @property
    def file_caches(self):
        return self.file_cache_model.objects.filter(session=self.session)

    def update_data(self, auth_key: bytes, dc_id: int, port: int, server_address: str, takeout_id: int):
        self.auth_key = auth_key
        self.dc_id = dc_id
        self.port = port
        self.server_address = server_address
        self.takeout_id = takeout_id
        self.save(update_fields=['auth_key', 'dc_id', 'port', 'server_address', 'takeout_id'])

    def update_state(self, state: State):
        self.state_pts = state.pts
        self.state_qts = state.qts
        self.state_date = state.date
        self.state_seq = state.seq
        self.state_saved = True
        self.save(update_fields=['state_pts', 'state_qts', 'state_date', 'state_seq', 'state_saved'])

    def get_state(self) -> Optional[State]:
        if self.state_saved:
            return State(
                pts=self.state_pts, qts=self.state_qts,
                date=self.state_date, seq=self.state_seq,
                unread_count=0,
            )

        return None

    def delete_with_entities(self):
        self.entities.delete()
        self.file_caches.delete()
        self.delete()

    def get_entities_list(self, ids: list):
        return list(self.entities.filter(entity_id__in=ids))

    def get_entity_by_value(self, multiple_rows=False, order_by=None, **kwargs):
        entities = self.entities.filter(**kwargs)

        if order_by:
            entities = entities.order_by()

        entities = entities.values_list('entity_id', 'hash_value')

        if not multiple_rows:
            entities = entities.first()

        return list(entities)

    def update_entities(self, old_entities, new_entities):
        if old_entities:
            self.entities.bulk_update(old_entities, ['hash_value', 'username', 'phone', 'name'])
        if new_entities:
            self.entities.bulk_create(new_entities)

    def get_file(self, md5_digest, file_size, cls):
        from its_utils.app_telethon.models.base_file_cache import FileType
        return self.file_caches.filter(
            md5_digest=md5_digest, file_size=file_size, file_type=FileType.from_type(cls).value,
        ).values_list(
            'pk', 'hash_value',
        ).first()

    def save_file(self, md5_digest, file_size, instance):
        from its_utils.app_telethon.models.base_file_cache import FileType
        self.file_caches.update_or_create(
            md5_digest=md5_digest, file_size=file_size,
            file_type=FileType.from_type(type(instance)).value,
            defaults={'hash_value': instance.access_hash, 'file_id': instance.id},
        )
