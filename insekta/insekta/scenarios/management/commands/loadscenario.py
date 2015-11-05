import sys

from django.core.management.base import BaseCommand, CommandError

from insekta.scenarios.models import Scenario, ScenarioError


class Command(BaseCommand):
    help = 'Load the specified scenario by key'

    def add_arguments(self, parser):
        parser.add_argument('key')

    def handle(self, *args, **options):
        try:
            scenario = Scenario.update_or_create_from_key(options['key'])
        except ScenarioError as e:
            raise CommandError(str(e))
        sys.stdout.write("Sucessfully loaded '{}': {}\n".format(
            options['key'], scenario.title))
