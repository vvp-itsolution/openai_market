from typing import TYPE_CHECKING

from telethon import utils
from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
from telethon.tl.types import InputDocument, InputPhoto, PeerChannel, PeerChat, PeerUser

if TYPE_CHECKING:
    from .models import BaseSessionData


class DjangoSession(MemorySession):
    def __init__(self, session_data: 'BaseSessionData'):
        super().__init__()

        self.session_data = session_data
        self._dc_id = session_data.dc_id
        self._server_address = session_data.server_address
        self._port = session_data.port
        self._takeout_id = session_data.takeout_id
        self._auth_key = AuthKey(data=session_data.auth_key) if session_data.auth_key else None

    def set_dc(self, dc_id, server_address, port):
        super().set_dc(dc_id, server_address, port)
        self._update_session_data()

    @MemorySession.auth_key.setter
    def auth_key(self, value):
        if self._auth_key == value:
            return

        self._auth_key = value
        self._update_session_data()

    @MemorySession.takeout_id.setter
    def takeout_id(self, value):
        if self._takeout_id == value:
            return

        self._takeout_id = value
        self._update_session_data()

    def _update_session_data(self):
        self.session_data.update_data(
            dc_id=self._dc_id,
            server_address=self._server_address,
            port=self._port,
            takeout_id=self._takeout_id,
            auth_key=self._auth_key.key if self._auth_key else b'',
        )

    def get_update_state(self, entity_id):
        return self.session_data.get_state()

    def set_update_state(self, entity_id, state):
        self.session_data.update_state(state)

    def save(self):
        pass

    def delete(self):
        self.session_data.delete_with_entities()

    def process_entities(self, tlo):
        rows = self._entities_to_rows(tlo)
        if not rows:
            return

        entities = self.session_data.get_entities_list(ids=[row[0] for row in rows])
        entities_map = {e.entity_id: e for e in entities}
        new_entities = []
        for row in rows:
            entity = entities_map.get(row[0])

            if entity:
                entity.hash_value = row[1]
                entity.username = row[2]
                entity.phone = row[3]
                entity.name = row[4]

            else:
                new_entities.append(
                    self.session_data.entity_model(
                        session=self.session_data.session,
                        entity_id=row[0], hash_value=row[1],
                        username=row[2], phone=row[3], name=row[4],
                    )
                )

        self.session_data.update_entities(
            old_entities=entities,
            new_entities=new_entities,
        )

    def get_entity_rows_by_username(self, username):
        entities = self.session_data.get_entity_by_value(
            multiple_rows=True, order_by='-date', username=username,
        )
        if len(entities) > 1:
            self.session_data.entities.filter(
                entity_id__in=[obj.entity_id for obj in entities[1:]],
            ).update(
                username=None,
            )

        return entities[0]

    def get_entity_rows_by_phone(self, phone):
        return self.session_data.get_entity_by_value(phone=phone)

    def get_entity_rows_by_name(self, name):
        return self.session_data.get_entity_by_value(name=name)

    def get_entity_rows_by_id(self, id, exact=True):
        if exact:
            return self.session_data.get_entity_by_value(entity_id=id)

        return self.session_data.get_entity_by_value(entity_id__in=[
            utils.get_peer_id(PeerUser(id)),
            utils.get_peer_id(PeerChat(id)),
            utils.get_peer_id(PeerChannel(id)),
        ])

    def get_file(self, md5_digest, file_size, cls):
        row = self.session_data.get_file(md5_digest, file_size, cls)
        return cls(*row) if row else None

    def cache_file(self, md5_digest, file_size, instance):
        if not isinstance(instance, (InputDocument, InputPhoto)):
            raise TypeError(f'Cannot cache {type(instance)} instance')

        self.session_data.save_file(md5_digest, file_size, instance)
