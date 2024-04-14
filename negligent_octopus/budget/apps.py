from django.apps import AppConfig


class BudgetConfig(AppConfig):
    name = "negligent_octopus.budget"
    verbose_name = "Budget"

    def ready(self):
        pass  # Requires it to be loaded first
