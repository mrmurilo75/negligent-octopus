from django.db import models
from django.db import transaction as db_transaction
from django.utils import timezone
from model_utils.models import SoftDeletableModel
from model_utils.models import TimeStampedModel

from negligent_octopus.users.models import User


class Category(TimeStampedModel, SoftDeletableModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)

    class Meta(TimeStampedModel.Meta, SoftDeletableModel.Meta):
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        unique_together = ["owner", "name"]


class Account(TimeStampedModel, SoftDeletableModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    initial_balance = models.FloatField(default=0.0)

    @property
    def balance(self):
        last_transaction = self.transaction_set.first()
        return last_transaction.balance if last_transaction else self.initial_balance

    def save(self, *args, **kwargs):
        try:
            old_model = self.__class__.objects.get(pk=self.pk)
            if (
                old_model.initial_balance != self.initial_balance
                and hasattr(self, "transaction_set")
                and self.transaction_set.last() is not None
            ):
                self.transaction_set.last().save()  # Trigger update balance
        except self.__class__.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

    class Meta(TimeStampedModel.Meta, SoftDeletableModel.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["-modified", "name"]
        unique_together = ["name", "owner"]


class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    balance = models.FloatField(editable=False, null=True)
    title = models.CharField(max_length=127)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def get_account_owner(self):
        return str(self.account.owner)

    def update_balance(self, last_transaction=None):
        if last_transaction is None:
            last_transaction = self.account.transaction_set.filter(
                models.Q(timestamp__lte=self.timestamp)
                & models.Q(created__lt=self.created),
            ).first()

        self.balance = self.amount
        if last_transaction is None:
            self.balance += self.account.initial_balance
        else:
            self.balance += last_transaction.balance

    @db_transaction.atomic
    def save(self, *args, update_balance=True, **kwargs):
        try:
            old_model = self.__class__.objects.get(pk=self.pk)
            if (
                old_model.timestamp != self.timestamp
                or old_model.account != self.account
            ):
                msg = "Cannot change fields 'account' or 'timestamp'."
                raise ValueError(msg)  # TODO: Change fields account or timestamp
        except self.__class__.DoesNotExist:
            old_model = None

        if not update_balance:
            super().save(*args, **kwargs)
            return

        self.update_balance()
        super().save(*args, **kwargs)

        if old_model and old_model.balance == self.balance:
            return

        universe = self.account.transaction_set.filter(
            models.Q(timestamp__gt=self.timestamp)
            | (models.Q(timestamp=self.timestamp) & models.Q(created__gt=self.created)),
        )

        previous = self
        for transaction in universe.reverse():
            transaction.update_balance(previous)
            transaction.save(update_balance=False)
            previous = transaction

    def __str__(self):
        return str(self.title)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-timestamp", "-created"]
        unique_together = ["timestamp", "created"]
