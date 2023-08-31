import asyncio

from sqlite3 import OperationalError

import telethon.sync


class TelegramClient(telethon.sync.TelegramClient):
    def __init__(self, *args, **kwargs):
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        super().__init__(*args, **kwargs)

    def __enter__(self) -> 'TelegramClient':
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.disconnect()
        except OperationalError:
            pass
