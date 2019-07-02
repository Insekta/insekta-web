import base64
import binascii
import random
import re

from django.utils.translation import ugettext_lazy as _


class BaseScript:
    def __init__(self, seed, task_identifier):
        self._seed = seed
        self._task_identifier = task_identifier

    def get_rng(self, domain=None):
        if domain is None:
            domain = self._task_identifier
        seed = self._seed.to_bytes(8, 'big')
        seed += domain.encode()
        r = random.Random()
        r.seed(seed)
        return r

    def validate(self, values):
        raise NotImplemented

    def generate(self):
        raise NotImplemented


class ScriptInputValidationError(Exception):
    pass


def safe_int(x):
    try:
        return int(x)
    except (ValueError, TypeError):
        raise ScriptInputValidationError(_('Input is not a valid integer.'))


def safe_float(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        raise ScriptInputValidationError(_('Input is not a valid real number.'))


def safe_hex(x, length=None):
    if x.startswith('0x'):
        x = x[2:]
    x = re.sub(r'\s+', '', x)
    try:
        retval = binascii.unhexlify(x)
    except binascii.Error:
        raise ScriptInputValidationError(_('Input is valid hex encoding.'))
    except ValueError:
        raise ScriptInputValidationError(_('Input contains non-hex characters '
                                           '(invisible unicode?).'))
    if length is not None and len(retval) != length:
        raise ScriptInputValidationError(_('Input did not match expected length.'))
    return retval


def safe_base64(x):
    try:
        return base64.b64decode(x)
    except (ValueError, TypeError):
        raise ScriptInputValidationError('Input is not valid base64.')


def regexp_string(regexp, x):
    if not isinstance(regexp, re.Pattern):
        regexp = re.compile(regexp)
    if not regexp.match(x):
        raise ScriptInputValidationError('Input does not match the expected format.')
