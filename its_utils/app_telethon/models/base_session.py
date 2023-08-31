import os
from typing import TYPE_CHECKING, Type, Optional, Union
import uuid

from asgiref.sync import sync_to_async, async_to_sync
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils.functional import cached_property

from telethon import events
from telethon.sessions import Session
from telethon.tl.custom import Dialog as TlDialog, Message as TlMessage
from telethon.tl.types import User as TlUser, Channel as TlChannel
from telethon.errors import (
    PhonePasswordFloodError, FloodWaitError, PhoneNumberInvalidError, PhoneCodeInvalidError,
    SessionPasswordNeededError, PasswordHashInvalidError,
)

from its_utils.app_model.abs_locker_model import AbsLockerModel, LockedTooLong, Locked
from its_utils.app_telethon.errors import SendCodeRequestError, SignInError
from its_utils.app_telethon.telegram_client import TelegramClient
from settings import ilogger

if TYPE_CHECKING:
    from its_utils.app_telethon.models import (
        BaseApplication, BaseUser, BaseDialog, BaseMessage, BaseSessionData, BaseEntity, BaseFileCache,
    )


def _uuid():
    return uuid.uuid4().hex


class BaseSession(models.Model, AbsLockerModel):
    USER_MODEL = NotImplemented  # type: Type[BaseUser]
    DIALOG_MODEL = NotImplemented  # type: Type[BaseDialog]
    MESSAGE_MODEL = NotImplemented  # type: Type[BaseMessage]

    # Для DjangoSession
    SESSION_DATA_MODEL = None  # type: Type[BaseSessionData]
    ENTITY_MODEL = None  # type: Type[BaseEntity]
    FILE_CACHE_MODEL = None  # type: Type[BaseFileCache]

    USE_DJANGO_SESSION = False
    SESSIONS_DIR = 'telethon_sessions'
    PARSE_MODE = 'html'  # or 'markdown'
    RECEIVE_UPDATES = False

    app = models.ForeignKey('TelethonApplication', on_delete=models.PROTECT)  # type: BaseApplication
    user = models.ForeignKey('TelethonUser', null=True, blank=True, on_delete=models.PROTECT)  # type: BaseUser
    session_id = models.CharField(max_length=32, default=_uuid, unique=True)
    is_deleted = models.BooleanField(default=False)
    dt_add = models.DateTimeField(auto_now=True, editable=True)
    last_loaded_message_date = models.DateTimeField(null=True, blank=True)
    lock_dt_to_load_history = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    class Admin(admin.ModelAdmin):
        list_display = 'app', 'user', 'is_deleted'
        list_display_links = list_display
        list_filter = 'is_deleted',

    def __str__(self):
        return self.session_id

    @cached_property
    def app_label(self) -> str:
        return type(self)._meta.app_label

    @cached_property
    def session_path(self) -> str:
        path = settings.BASE_DIR

        if self.SESSIONS_DIR:
            path = os.path.join(path, self.SESSIONS_DIR)
            if not os.path.exists(path):
                os.makedirs(path)

        return os.path.join(path, '{}'.format(self.session_id))

    def _get_session(self) -> Union[str, Session]:
        if self.USE_DJANGO_SESSION:
            assert self.SESSION_DATA_MODEL, 'SESSION_DATA_MODEL is not set'
            assert self.ENTITY_MODEL, 'ENTITY_MODEL is not set'
            assert self.ENTITY_MODEL, 'SENT_FILE_MODEL is not set'

            from its_utils.app_telethon.django_session import DjangoSession
            return DjangoSession(self.get_django_session_data())

        return self.session_path

    def get_django_session_data(self) -> 'BaseSessionData':
        data, _ = self.SESSION_DATA_MODEL.objects.get_or_create(session=self)
        return data

    def get_client(self) -> TelegramClient:
        client = TelegramClient(
            self._get_session(), self.app.api_id, self.app.api_hash,
            sequential_updates=True, receive_updates=self.RECEIVE_UPDATES,
        )
        client.parse_mode = self.PARSE_MODE
        return client

    def send_code_request(self, phone: str) -> str:
        with self.get_client() as client:
            try:
                return client.send_code_request(phone).phone_code_hash

            except (PhonePasswordFloodError, FloodWaitError) as exc:
                raise SendCodeRequestError('Слишком много попыток входа. Попробуйте позже.', caused_by=exc)

            except (PhoneNumberInvalidError, TypeError) as exc:
                raise SendCodeRequestError('Неверный номер телефона.', caused_by=exc)

    def sign_in(self, phone: str, code: str = None, password: str = None, phone_code_hash: str = None):
        with self.get_client() as client:
            try:
                client.sign_in(phone=phone, code=code, password=password, phone_code_hash=phone_code_hash)

            except (PhonePasswordFloodError, FloodWaitError) as exc:
                raise SignInError('Слишком много попыток входа. Попробуйте позже.', caused_by=exc)

            except PhoneCodeInvalidError as exc:
                raise SignInError('Неверный код.', caused_by=exc)

            except SessionPasswordNeededError as exc:
                raise SignInError('Необходимо ввести пароль.', caused_by=exc, password_required=True)

            except PasswordHashInvalidError as exc:
                raise SignInError('Неверный пароль.', caused_by=exc, password_required=True)

            user = client.get_me()

        self._update_user(user)

    def sign_out(self):
        with self.get_client() as client:
            if client.is_user_authorized():
                client.log_out()
            client.session.close()
            client.session.delete()

        self._update_user(None)

    def get_me(self) -> Optional['BaseUser']:
        with self.get_client() as client:
            user = client.get_me()

        self._update_user(user)
        return self.user

    def _update_user(self, tl_user: TlUser = None):
        self.user = self.USER_MODEL.from_tl_user(tl_user) if tl_user else None
        self.is_deleted = not self.user
        self.save(update_fields=['user', 'is_deleted'])

    def load_history(self):
        try:
            with self.lock_with_field('lock_dt_to_load_history', 240):
                result = self._load_history()
                return 'new messages: {}'.format(result)

        except LockedTooLong:
            ilogger.error('telethon_load_history_lock_{}'.format(self.app_label), str(self))
            return 'LockedTooLong'

        except Locked:
            return 'Locked'

        except Exception as exc:
            ilogger.error('telethon_load_history_error_{}'.format(self.app_label), '{}: {}'.format(self, exc))
            return 'Error! {}'.format(exc)

    def _load_history(self) -> int:
        new_messages = 0

        last_loaded_message_date = self.last_loaded_message_date
        with self.get_client() as client:
            for tl_dialog in client.iter_dialogs():  # type: TlDialog
                # диалоги отсортированы по дате последнего сообщения

                if not self.last_loaded_message_date:
                    # первый запуск
                    last_loaded_message_date = tl_dialog.date
                    break

                if tl_dialog.date <= self.last_loaded_message_date:
                    # нашли диалог без изменений
                    break

                dialog = self.DIALOG_MODEL.from_tl_dialog(self, tl_dialog, client=client)
                tl_messages = client.iter_messages(
                    tl_dialog.entity, offset_date=self.last_loaded_message_date, reverse=True,
                )
                for tl_message in tl_messages:  # type: TlMessage
                    if isinstance(tl_message.sender, TlChannel):
                        # todo: обрабатывать сообщения каналов
                        continue

                    sender = self.USER_MODEL.from_tl_user(tl_message.sender or tl_dialog)
                    message = self.MESSAGE_MODEL.from_tl_chat(dialog, sender, tl_message)

                    try:
                        self.on_new_message(message)
                    except Exception as exc:
                        ilogger.error(
                            'telethon_on_new_message_error_{}'.format(self.app_label),
                            'message {}: {}'.format(message.id, exc),
                        )

                    new_messages += 1
                    last_loaded_message_date = max(tl_message.date, last_loaded_message_date)

        self.last_loaded_message_date = last_loaded_message_date
        self.save(update_fields=['last_loaded_message_date'])
        return new_messages

    def _catch_up(self) -> str:
        with self.get_client() as client:
            client.add_event_handler(
                sync_to_async(self._on_new_message_event),
                events.NewMessage(incoming=True),
            )
            client.catch_up()

        return 'ok'

    def _on_new_message_event(self, event):
        ilogger.debug('telethon_new_message_event_{}'.format(self.app_label), 'session {}: {}'.format(self.id, event))

        try:
            tl_sender = async_to_sync(event.get_sender)()
            tl_message = event.message  # type: TlMessage

            if not isinstance(tl_message.sender, TlUser):
                # todo: обрабатывать сообщения каналов
                return

            try:
                dialog = self.DIALOG_MODEL.objects.get(session=self, dialog_id=tl_message.chat_id)

            except self.DIALOG_MODEL.DoesNotExist:
                with self.get_client() as client:
                    # fixme: это очень медленно
                    tl_dialog = client.get_dialogs(limit=1, offset_id=tl_message.chat_id)
                    tl_dialog = tl_dialog[0]

                dialog = self.DIALOG_MODEL.from_tl_dialog(self, tl_dialog)

            sender = self.USER_MODEL.from_tl_user(tl_sender)
            message = self.MESSAGE_MODEL.from_tl_chat(dialog, sender, tl_message)

        except Exception as exc:
            ilogger.error(
                'telethon_new_message_event_error_{}'.format(self.app_label),
                'session {}: {}\n{}'.format(self.id, event, exc),
            )
            return

        try:
            self.on_new_message(message)
        except Exception as exc:
            ilogger.error(
                'telethon_on_new_message_error_{}'.format(self.app_label),
                'message {}: {}'.format(message.id, exc),
            )

    def on_new_message(self, message: 'BaseMessage'):
        pass
