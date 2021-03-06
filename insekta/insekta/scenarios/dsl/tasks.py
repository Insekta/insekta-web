import base64
import hashlib
import hmac
from inspect import signature

from django.conf import settings
from django.contrib.auth import get_user_model
from nacl.secret import SecretBox
from nacl.exceptions import CryptoError

from insekta.scenarios.dsl.scripts import ScriptInputValidationError


__all__ = ['TemplateTaskError', 'TemplateTask', 'MultipleChoiceTask', 'Choice',
           'QuestionTask', 'task_classes']


class TemplateTaskError(Exception):
    pass


class TemplateTask:
    must_remember_answer = False

    def __init__(self, identifier):
        self.order_id = 1
        self.identifier = identifier

    def check_for_errors(self):
        raise NotImplemented

    def validate(self, values, validation_context):
        raise NotImplemented

    def extract_values(self, user, scenario, form_values):
        raise NotImplemented

    def get_mac(self, user, scenario):
        mac_msg = 'templatetask:{}:{}:{}'.format(user.pk, scenario.pk, self.identifier)
        return hmac.new(settings.SECRET_KEY.encode(), mac_msg.encode(),
                        hashlib.sha256).hexdigest()


class MultipleChoiceTask(TemplateTask):
    task_type = 'multiple_choice'

    def __init__(self, identifier, **kwargs):
        super().__init__(identifier)
        self.choices = {}

    def check_for_errors(self):
        if not self.choices:
            raise TemplateTaskError('Empty choices')

    def extract_values(self, user, scenario, form_values):
        values = {}
        for choice in self.choices.values():
            choice_mac = choice.get_mac(user, scenario, self.identifier)
            values[choice.name] = bool(form_values.get(choice_mac))
        return values

    def validate(self, values, validation_context):
        for choice in self.choices.values():
            if values[choice.name] != choice.correct:
                return False
        return True

    def __repr__(self):
        return '{}(choices={!r})'.format(self.__class__.__name__, self.choices)


class SingleChoiceTask(TemplateTask):
    task_type = 'single_choice'

    def __init__(self, identifier, **kwargs):
        super().__init__(identifier)
        self.choices = {}

    def check_for_errors(self):
        if not self.choices:
            raise TemplateTaskError('Empty choices')

        num_correct = 0
        for choice in self.choices.values():
            if choice.correct:
                num_correct += 1
        if num_correct != 1:
            raise TemplateTaskError('Require exactly 1 correct answer.')

    def extract_values(self, user, scenario, form_values):
        values = {'answer': None}
        for choice in self.choices.values():
            choice_mac = choice.get_mac(user, scenario, self.identifier)
            if form_values.get('answer') == choice_mac:
                values['answer'] = choice.name
                break
        return values

    def validate(self, values, validation_context):
        if values['answer'] is None:
            return False
        return self.choices[values['answer']].correct

    def __repr__(self):
        return '{}(choices={!r})'.format(self.__class__.__name__, self.choices)


class Choice:
    def __init__(self, name, correct=False, **kwargs):
        self.name = name
        self.correct = correct

    def get_mac(self, user, scenario, task_identifier):
        mac_msg = 'choice:{}:{}:{}:{}'.format(user.pk, scenario.pk, task_identifier, self.name)
        return hmac.new(settings.SECRET_KEY.encode(), mac_msg.encode(),
                        hashlib.sha256).hexdigest()

    def __repr__(self):
        return '{}(name={!r}, correct={!r})'.format(self.__class__.__name__,
                                                    self.name,
                                                    self.correct)


class QuestionTask(TemplateTask):
    task_type = 'question'

    def __init__(self, identifier, case_sensitive=False, strip=True, **kwargs):
        super().__init__(identifier)
        self.answers = []
        self.case_sensitive = case_sensitive
        self.strip = strip

    def check_for_errors(self):
        if not self.answers:
            raise TemplateTaskError('No answers')
        if not isinstance(self.case_sensitive, bool):
            raise TemplateTaskError('Attribute "case_sensitive" must be of type bool')
        if not isinstance(self.strip, bool):
            raise TemplateTaskError('Attribute "strip" must be of type bool')

    def extract_values(self, user, scenario, form_values):
        return {'answer': form_values.get('answer', '')}

    def validate(self, values, validation_context):
        answer = values['answer']
        if self.strip:
            answer = answer.strip()
        if not self.case_sensitive:
            answer = answer.lower()
    
        for expected_answer in self.answers:
            if self.strip:
                expected_answer = expected_answer.strip()
            if not self.case_sensitive:
                expected_answer = expected_answer.lower()
            if answer == expected_answer:
                return True
        return False

    def __repr__(self):
        return '{}(answers={!r}, case_sensitive={!r}, strip={!r})'.format(
            self.__class__.__name__, self.answers, self.case_sensitive, self.strip)


class ScriptTask(TemplateTask):
    task_type = 'script'
    must_remember_answer = True

    def __init__(self, identifier, script_name, scenario, **kwargs):
        super().__init__(identifier)
        self.script_name = script_name
        self.scenario = scenario
        self.fields = set()

    def check_for_errors(self):
        if not self.fields:
            raise TemplateTaskError('Empty fields in script')

    def extract_values(self, user, scenario, form_values):
        values = {key: value for key, value in form_values.items()
                  if key in self.fields}
        for field in self.fields:
            if field not in values:
                values[field] = None
        values['_seed'] = user.pk
        return values

    def validate(self, values, validation_context):
        script_instance = self._get_script_instance(values['_seed'])
        if len(signature(script_instance.validate).parameters) == 2:
            is_valid = script_instance.validate(values, validation_context)
        else:
            is_valid = script_instance.validate(values)
        if not is_valid:
            raise ScriptInputValidationError(None)
        return is_valid

    def get_values(self, user):
        script_instance = self._get_script_instance(user.pk)
        return script_instance.generate()

    def _get_script_instance(self, seed):
        script_classes = self.scenario.get_script_classes()
        try:
            class_obj = script_classes[self.script_name]
        except KeyError:
            raise TemplateTaskError('No such script: {}'.format(self.script_name))
        return class_obj(seed, self.identifier)

    def get_download_key(self, user, filename):
        box = ScriptTask.get_secretbox()
        msg = '{}:{}:{}:{}'.format(self.script_name, user.pk, self.identifier,
                                   filename).encode()
        return base64.b32encode(box.encrypt(msg)).decode().rstrip('=')

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.identifier)

    @staticmethod
    def decrypt_download_key(download_key):
        User = get_user_model()
        box = ScriptTask.get_secretbox()
        if len(download_key) % 8:
            download_key = download_key + ('=' * (8 - (len(download_key) % 8)))
        try:
            pt = box.decrypt(base64.b32decode(download_key)).decode()
            script_name, user_pk, task_identifier, filename = pt.split(':', 3)
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                raise ValueError('Invalid user')
        except (ValueError, CryptoError):
            raise ValueError('Invalid download')
        return script_name, user, task_identifier, filename

    @staticmethod
    def get_secretbox():
        secret_bytes = settings.SECRET_KEY.encode()
        key = hashlib.sha256(b'scriptdownload\x00' + secret_bytes).digest()
        return SecretBox(key)


task_classes = {
    MultipleChoiceTask.task_type: MultipleChoiceTask,
    SingleChoiceTask.task_type: SingleChoiceTask,
    QuestionTask.task_type: QuestionTask,
    ScriptTask.task_type: ScriptTask
}
