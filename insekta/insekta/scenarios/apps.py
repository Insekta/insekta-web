import importlib

from django.apps import AppConfig
from django.conf import settings


class ScenariosConfig(AppConfig):
    name = 'insekta.scenarios'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.script_classes = {}

    def ready(self):
        self._load_script_classes()

    def _load_script_classes(self):
        for import_path in settings.SCENARIO_SCRIPT_CLASSES:
            mod = importlib.import_module(import_path)
            if not hasattr(mod, 'script_classes'):
                raise ValueError('Module {} is missing script_classes'.format(
                    import_path
                ))
            for key, class_obj in mod.script_classes.items():
                self.script_classes[key] = class_obj
