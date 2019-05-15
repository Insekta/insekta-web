import re

from jinja2 import Environment, nodes

from insekta.scenarios.dsl.tasks import Choice, TemplateTaskError, task_classes


__all__ = ['ParserError', 'TaskParser']


class ParserError(Exception):
    def __init__(self, msg, lineno):
        super().__init__(msg)
        self.lineno = lineno


class TaskParser:
    valid_identifier = re.compile('^[a-z]+[a-z0-9_]*$')
    valid_task_types = ('multiple_choice', 'question')

    def __init__(self, ast, scenario):
        self.ast = ast
        self._task = None
        self._scenario = scenario

    def get_tasks(self):
        tasks = {}
        for callblock_node in self.ast.find_all(nodes.CallBlock):
            call_node = callblock_node.call
            call_name = call_node.node.name
            if call_name != 'task':
                continue
            kwargs = self._parse_kwargs(call_node)
            if 'identifier' not in kwargs:
                raise ParserError('Missing identifier in task on line {}'.format(
                    call_node.lineno), call_node.lineno)
            if not self.valid_identifier.match(kwargs['identifier']):
                raise ParserError('Invalid identifier in task on line {}'.format(
                    call_node.lineno), call_node.lineno)
            if 'type' not in kwargs:
                raise ParserError('Missing type in task on line {}'.format(
                    call_node.lineno), call_node.lineno)
            if kwargs['type'] not in task_classes:
                raise ParserError('Invalid type in task on line {}'.format(
                    call_node.lineno), call_node.lineno)
            kwargs['scenario'] = self._scenario

            self._task = task_classes[kwargs['type']](**kwargs)

            for child_node in callblock_node.body:
                self._visit_node(child_node)
            try:
                self._task.check_for_errors()
            except TemplateTaskError as e:
                raise ParserError('Invalid task on line {}: {}'.format(
                    call_node.lineno, e), call_node.lineno)
            tasks[self._task.identifier] = self._task
            self._task = None
        return tasks

    def _visit_node(self, node: nodes.Node):
        if isinstance(node, nodes.Call):
            call_name = node.node.name
            if call_name == 'task':
                raise ParserError('Nested tasks are not allowed on line {}'.format(
                    node.lineno), node.lineno)
            elif call_name == 'choice':
                self._handle_choice(node)
                return
            elif call_name == 'answer':
                self._handle_answer(node)
                return
            elif call_name == 'script_input':
                self._handle_script_input(node)
                return

        for child_node in node.iter_child_nodes():
            self._visit_node(child_node)

    def _handle_choice(self, node: nodes.Node):
        kwargs = self._parse_kwargs(node)

        if 'name' not in kwargs:
            raise ParserError('Choice attribute "name" is required (line {})'.format(
                node.lineno), node.lineno)
        if not isinstance(kwargs['name'], str):
            raise ParserError('Choice attribute "name" must be of type str (line {})'.format(
                node.lineno), node.lineno)
        if not self.valid_identifier.match(kwargs['name']):
            raise ParserError('Choice attribute "name" is invalid (line {})'.format(
                node.lineno), node.lineno)

        correct = kwargs.get('correct', False)
        if not isinstance(correct, bool):
            raise ParserError('Choice attribute "correct" must be bool (line {})'.format(
                node.lineno), node.lineno)

        choice = Choice(**kwargs)
        self._task.choices[choice.name] = choice

    def _handle_answer(self, node: nodes.Node):
        kwargs = self._parse_kwargs(node)

        if self._task.answers:
            raise ParserError('Duplicate answer call (line {})'.format(
                node.lineno), node.lineno)
        if 'expected' not in kwargs:
            raise ParserError('Answer attribute "expected" is required (line {})'.format(
                node.lineno), node.lineno)
        if not isinstance(kwargs['expected'], (list, str)):
            raise ParserError('Answer attribute "expected" is not str/list (line {})'.format(
                node.lineno), node.lineno)

        answers = kwargs['expected']
        if not isinstance(answers, list):
            answers = [answers]
        self._task.answers = answers

    def _handle_script_input(self, node: nodes.Node):
        kwargs = self._parse_kwargs(node)
        if 'name' not in kwargs:
            raise ParserError('script_input attribute "name" is required (line {})'.format(
                node.lineno), node.lineno)
        self._task.fields.add(kwargs['name'])

    @staticmethod
    def _parse_kwargs(node: nodes.Node):
        kwargs = {}
        for keyword in node.kwargs:
            if isinstance(keyword.value, nodes.Const):
                kwargs[keyword.key] = keyword.value.value
            elif isinstance(keyword.value, nodes.List): 
                kwargs[keyword.key] = [] 
                for elem in keyword.value.items: 
                    kwargs[keyword.key].append(elem.value)
        return kwargs

    @classmethod
    def from_filename(cls, filename, scenario):
        env = Environment()
        with open(filename) as f:
            template_source = f.read()
        return cls(env.parse(template_source), scenario)
