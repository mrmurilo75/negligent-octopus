from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from negligent_octopus.budget.models import ImportActivo

last = ImportActivo.objects.last().load
with (Path(settings.MEDIA_ROOT) / Path(last.name)).open("rb") as xslx:
    pd.read_excel(
        xslx,
        skiprows=7,
        names=[
            "date_of_movement",
            "date_of_process",
            "description",
            "value",
            "balance",
        ],
    )


class Command(BaseCommand):
    help = "Import transactions from an ActivoBank export."

    def handle(self, *args, **kwargs):
        pass
