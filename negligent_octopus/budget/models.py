from datetime import datetime
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from model_utils.models import TimeStampedModel

from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Transaction
from negligent_octopus.utils import get_filename_extension
from negligent_octopus.utils import get_filename_no_extension
from negligent_octopus.utils.validators import FileExtensionValidator


def upload_import_file_to(instance, filename):
    return (
        f"{slugify(instance.owner)}--{instance.owner.pk}/"
        f"{instance.account}/"
        f"{instance.created}/"
        f"{instance.name}.{get_filename_extension(instance.load.name)}"
    )


class SimpleImportedTransaction(TimeStampedModel):
    loaded_from = models.ForeignKey(
        "SimpleTransactionsImport",
        on_delete=models.RESTRICT,
    )
    date = models.DateField()
    title = models.CharField(max_length=255)
    amount = models.FloatField()
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.validated and not self.transaction:
            self.transaction = Transaction.objects.create(
                account=self.loaded_from.account,
                amount=self.amount,
                timestamp=datetime.combine(
                    self.date,
                    datetime.min.time(),
                    tzinfo=timezone.get_current_timezone(),
                ),
                balance=self.balance,
                title=self.title,
            )
            kwargs["update_fields"] = {"transaction", "validated"}
            super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Simple Imported Transaction"
        verbose_name_plural = "Simple Imported Transactions"
        ordering = ["-date", "-created"]


class SimpleTransactionsImport(TimeStampedModel):
    READABLE_EXTENSIONS = {
        "csv": pd.read_csv,
        "xsls": pd.read_excel,
        "xls": pd.read_excel,
        "xlsx": pd.read_excel,
        "xlsm": pd.read_excel,
        "xlsb": pd.read_excel,
    }
    child_transaction_class = SimpleImportedTransaction
    child_transaction_related_name = None

    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    load = models.FileField(
        upload_to=upload_import_file_to,
        validators=[
            FileExtensionValidator(tuple(READABLE_EXTENSIONS.keys())),
        ],
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
    )
    processed = models.BooleanField(default=False)

    @property
    def child_transaction_manager(self):
        if self.child_transaction_related_name is not None:
            return getattr(self, self.child_transaction_related_name)
        return getattr(
            self,
            f"{self.child_transaction_class.__name__.lower()}_set",
        )

    def _set_name_from_filename(self):
        try:
            name = self.load.name.rsplit("/", 1)[1]
        except IndexError:
            name = self.load.name
        self.name = get_filename_no_extension(name)

    def create_imported_transactions(
        self,
        read_func_args=None,
        read_func_kwargs=None,
        *,
        row_to_model=lambda **x: x,
        commit=True,
    ):
        if read_func_args is None:
            read_func_args = ()
        if read_func_kwargs is None:
            read_func_kwargs = {
                "names": [
                    "date",
                    "title",
                    "amount",
                    "balance",
                ],
                "header": 0,
            }

        transactions = []
        with (Path(settings.MEDIA_ROOT) / Path(self.load.name)).open("rb") as data_file:
            extension = self.load.name.rsplit(".", 1)[1]
            read_file = self.READABLE_EXTENSIONS[extension]
            data = read_file(
                data_file,
                *read_func_args,
                **read_func_kwargs,
            )

        for _i, row in data.iterrows():
            values = row_to_model(**row)
            try:
                self.child_transaction_manager.get(**values)
            except self.child_transaction_class.DoesNotExist:
                # TODO Pass in relevant args, kwargs
                transaction = self.child_transaction_class(
                    loaded_from=self,
                    **values,
                )
                transactions.append(transaction)

                if commit:
                    transaction.save()

        return transactions

    def save(self, *args, **kwargs):
        if not self.name:
            self._set_name_from_filename()
        super().save(*args, **kwargs)

        if not self.processed:
            self.create_imported_transactions(commit=True)
            self.processed = True
            kwargs["update_fields"] = {"processed"}
            super().save(*args, **kwargs)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Simple Transactions Import"
        verbose_name_plural = "Simple Imports"
        ordering = ["-created"]
