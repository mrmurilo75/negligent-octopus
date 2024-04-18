from django.db import models
from django.utils.text import slugify
from model_utils.models import TimeStampedModel

from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Transaction
from negligent_octopus.users.models import User
from negligent_octopus.utils import get_filename_extension
from negligent_octopus.utils import get_filename_no_extension
from negligent_octopus.utils.validators import FileExtensionValidator


def upload_activo_import_to(instance, filename):
    return (
        f"{slugify(instance.owner)}--{instance.owner.pk}/"
        f"{instance.account}/"
        f"{instance.created}/"
        f"{instance.name}.{get_filename_extension(instance.load.name)}"
    )


class ImportActivo(TimeStampedModel):
    # TODO deal with each when importing - for activo we only deal with excel
    ALLOWED_EXTENSIONS = (
        "csv",
        "xsls",
        "xls",
        "xlsx",
        "xlsm",
        "xlsb",
        "odf",
        "ods",
        "odt",
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    load = models.FileField(
        upload_to=upload_activo_import_to,
        validators=[
            FileExtensionValidator(ALLOWED_EXTENSIONS),
        ],
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
    )
    processed = models.BooleanField(default=False)

    def _set_name_from_filename(self):
        try:
            name = self.load.name.rsplit("/", 1)[1]
        except IndexError:
            name = self.load.name
        self.name = get_filename_no_extension(name)

    def save(self, *args, **kwargs):
        if not self.name:
            self._set_name_from_filename()
        super().save(*args, **kwargs)

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
    balance = models.FloatField()
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
