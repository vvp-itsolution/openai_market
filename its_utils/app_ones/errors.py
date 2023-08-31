from requests import Response


class BaseOneSError(Exception):
    pass


class OneSClientError(BaseOneSError):
    def __init__(self, response: Response):
        self.response = response

    def __str__(self):
        return '[{}] {}'.format(self.response.status_code, self.response.text[:200])
