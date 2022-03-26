from typing import NamedTuple


class NoneCallback(NamedTuple):
    text: str = 'None'
    func: object = lambda: None