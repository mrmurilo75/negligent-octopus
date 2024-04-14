from django.db import models
from model_utils.models import TimeStampedModel

from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Transaction
from negligent_octopus.users.models import User
from negligent_octopus.utils.validators import FileExtensionValidator


def upload_activo_import_to(instance, filename):
    return (
        f"{instance.owner}/{instance.account}/{instance.modified}/{instance.filename}"
    )


class ImportActivo(TimeStampedModel):
    ALLOWED_EXTENSIONS = ("csv", "xsls")

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    load = models.FileField(
        upload_to=upload_activo_import_to,
        validators=[FileExtensionValidator(ALLOWED_EXTENSIONS)],
        blank=True,
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    processed = models.BooleanField(default=False)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Activo Import"
        verbose_name_plural = "Activo Imports"
        ordering = ["created"]


class ImportedActivoTransaction(TimeStampedModel):
    loaded_from = models.ForeignKey(ImportActivo, on_delete=models.RESTRICT)
    date_of_movement = models.DateField()
    date_of_process = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    value = models.FloatField()
    balance = models.FloatField(null=True, blank=True)
    validated = models.BooleanField(default=False)
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def get_load_owner(self):
        return str(self.loaded_from.owner)

    def has_transaction(self):
        return self.transaction is not None

    def __str__(self):
        return str(self.description)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Imported Activo Transaction"
        verbose_name_plural = "Imported Activo Transactions"
        ordering = ["-date_of_process", "-created"]
