from django.db import models
from django.db import transaction as db_transaction
from django.utils import timezone
from django.utils.functional import cached_property
from model_utils.models import SoftDeletableModel
from model_utils.models import TimeStampedModel

from negligent_octopus.users.models import User


class Account(TimeStampedModel, SoftDeletableModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    @cached_property
    def balance(self):
        return self.transaction_set.first().balance

    def __str__(self):
        return str(self.name)

    class Meta(TimeStampedModel.Meta, SoftDeletableModel.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["-modified", "name"]


class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    balance = models.FloatField(editable=False, null=True)
    title = models.CharField(max_length=127)
    description = models.TextField(blank=True)

    def get_account_owner(self):
        return str(self.account.owner)

    @db_transaction.atomic
    def save(self, *args, **kwargs):
        old_model = self.__class__.objects.get(pk=self.pk)
        if old_model.timestamp != self.timestamp or old_model.account != self.account:
            msg = "Cannot change fields 'account' or 'timestamp'."
            raise ValueError(msg)  # TODO: Change fields account or timestamp

        if old_model.amount != self.amount:
            msg = "Cannot change field 'amount'."
            raise ValueError(msg)
            # TODO: Id what trans is (del, change, create) and calculate for approp amt

        if self.balance is None:
            self.balance = self.amount
            last_transaction = self.account.transaction_set.filter(
                models.Q(timestamp__lte=self.timestamp)
                & models.Q(created__lt=self.created),
            ).first()
            if last_transaction is not None:
                self.balance += last_transaction.balance

            universe = self.account.transaction_set.filter(
                models.Q(timestamp__gte=self.timestamp)
                & models.Q(created__gt=self.created),
            ).reverse()

            previous = universe.first()
            for transaction in universe:
                if transaction == universe.first():
                    continue
                transaction.balance = transaction.amount + previous.balance
                transaction.save()
                previous = transaction

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-timestamp", "-created"]
        unique_together = ["timestamp", "created"]
