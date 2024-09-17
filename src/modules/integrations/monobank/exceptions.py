class MonobankException(Exception):
    pass


class TooManyRequests(MonobankException):
    pass


class UnknownError(MonobankException):
    pass
