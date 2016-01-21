import os

from jinja2 import TemplateNotFound
from jinja2.loaders import BaseLoader


class ScenarioTemplateLoader(BaseLoader):
    def __init__(self, scenario_dir):
        self.scenario_dir = scenario_dir

    def get_source(self, environment, template):
        filename = os.path.join(self.scenario_dir, template, 'scenario.html')
        try:
            with open(filename) as f:
                contents = f.read()
            mtime = os.path.getmtime(filename)
        except (IOError, OSError):
            raise TemplateNotFound(template)

        def uptodate():
            try:
                os.path.getmtime(filename) == mtime
            except OSError:
                return False

        return contents, template, uptodate

    def list_templates(self):
        return os.listdir(self.scenario_dir)
