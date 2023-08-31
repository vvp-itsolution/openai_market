from telethon.errors import SessionPasswordNeededError


class BaseAppTelethonError(Exception):
    def __init__(self, message: str = None, caused_by: Exception = None):
        self.message = message
        self.caused_by = caused_by

    def __str__(self):
        return self.message or type(self).__class__.__name__


class SendCodeRequestError(BaseAppTelethonError):
    pass


class SignInError(BaseAppTelethonError):
    def __init__(self, *args, password_required: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.password_required = password_required

    def is_password_needed_error(self):
        return isinstance(self.caused_by, SessionPasswordNeededError)
