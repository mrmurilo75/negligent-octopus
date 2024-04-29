from django.apps import AppConfig


class BudgetConfig(AppConfig):
    name = "negligent_octopus.alpha_prototype"
    verbose_name = "Prototype (Alpha)"

    def ready(self):
        pass
