import base64
import binascii
import random
import re


class BaseScript:
    def __init__(self, seed):
        self._seed = seed

    def get_rng(self, domain=None):
        if domain is None:
            domain = self.__class__.__name__
        seed = self._seed.to_bytes(8, 'big')
        seed += domain.encode()
        r = random.Random()
        r.seed(seed)
        return r

    def validate(self, values):
        raise NotImplemented

    def generate(self):
        raise NotImplemented


class InvalidUserInputError(Exception):
    pass


def safe_int(x):
    try:
        return int(x)
    except (ValueError, TypeError):
        raise InvalidUserInputError()


def safe_float(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        raise InvalidUserInputError()


def safe_hex(x):
    if x.startswith('0x'):
        x = x[2:]
    try:
        return binascii.unhexlify(x)
    except binascii.Error:
        raise InvalidUserInputError()


def safe_base64(x):
    try:
        return base64.b64decode(x)
    except (ValueError, TypeError):
        raise InvalidUserInputError()


def regexp_string(regexp, x):
    if not isinstance(regexp, re.Pattern):
        regexp = re.compile(regexp)
    if not regexp.match(x):
        raise InvalidUserInputError()
