from django.db import models
from django.db import transaction as db_transaction
from django.utils import timezone
from model_utils.models import SoftDeletableModel
from model_utils.models import TimeStampedModel
from model_utils.tracker import FieldTracker

from negligent_octopus.users.models import User


class Account(TimeStampedModel, SoftDeletableModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    @property
    def balance(self):
        return self.transaction_set.last().balance

    def __str__(self):
        return str(self.name)

    class Meta(TimeStampedModel.Meta, SoftDeletableModel.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["-modified", "name"]


class Transaction(TimeStampedModel):
    amount = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    balance = models.FloatField(default=0.0, editable=False)
    title = models.CharField(max_length=127)
    description = models.TextField(blank=True)

    tracker = FieldTracker(
        fields=["amount", "timestamp"],
    )  # We need to consider changes to the timestamp
    # and how to update balances based on these

    def get_account_owner(self):
        return str(self.account.owner)

    @db_transaction.atomic
    def save(self, *args, **kwargs):
        universe = self.account.transaction_set

        last_transaction = (
            universe.filter(
                timestamp__lte=self.timestamp,
            )
            .order_by("-created")
            .first()
        )
        self.balance = last_transaction.balance + self.amount
        super().save(*args, **kwargs)
        last_transaction = self

        to_update = universe.filter(
            timestamp__gte=self.timestamp,
        ).exclude(
            created__lt=self.created,
        )
        for transaction in to_update:
            transaction.balance = last_transaction.balance + transaction.amount
            transaction.save()
            last_transaction = transaction

    def delete(self, *args, **kwargs):
        self.amount = -self.amount
        self.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["timestamp", "-modified"]
        unique_together = ["timestamp", "created"]
