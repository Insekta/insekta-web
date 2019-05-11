import hashlib
import hmac

from django.conf import settings


__all__ = ['TemplateTaskError', 'TemplateTask', 'MultipleChoiceTask', 'Choice',
           'QuestionTask', 'task_classes']


class TemplateTaskError(Exception):
    pass


class TemplateTask:
    def __init__(self, identifier):
        self.identifier = identifier

    def check_for_errors(self):
        raise NotImplemented

    def validate(self, values):
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

    def validate(self, values):
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

    def validate(self, values):
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

    def validate(self, values):
        answer = values['answer']
        if self.strip:
            answer = answer.strip()
        if not self.case_sensitive:
            answer = answer.lower()
    
        print('magic', self.answers)
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


task_classes = {
    MultipleChoiceTask.task_type: MultipleChoiceTask,
    SingleChoiceTask.task_type: SingleChoiceTask,
    QuestionTask.task_type: QuestionTask
}
