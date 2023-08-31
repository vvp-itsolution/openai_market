from django.http import HttpResponse


class BitrixChatBotException(Exception):
    def __init__(self, message, http_status=400):
        self.message = message
        self.http_status = http_status

    def http_response(self):
        return HttpResponse(self.message, status=self.http_status)


class EventVerificationError(BitrixChatBotException):
    def __init__(self, message='Verification failed'):
        super().__init__(message, 401)
