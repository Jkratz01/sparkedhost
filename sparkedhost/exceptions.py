class SparkedHostError(Exception):
    pass


class AuthenticationError(SparkedHostError):
    pass


class NotFoundError(SparkedHostError):
    pass


class APIError(SparkedHostError):
    def __init__(self, status_code, message, body=None):
        self.status_code = status_code
        self.body = body
        super().__init__(f"API error {status_code}: {message}")
