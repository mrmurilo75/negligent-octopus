from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import transactions from an ActivoBank export."

    def handle(self, *args, **kwargs):
        pass
