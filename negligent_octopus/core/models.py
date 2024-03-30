from typing import Optional

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
        previous_transaction = self.transaction_set.first()
        return (
            previous_transaction.balance
            if previous_transaction
            else self.initial_balance
        )

    def save(self, *args, **kwargs):
        try:
            old_instance = self.__class__.objects.get(pk=self.pk)
            if (
                old_instance.initial_balance != self.initial_balance
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
    destination_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="transfer_set",
        null=True,
    )
    transfer_transaction = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        related_name="+",
        unique=True,  # OneToOne
        null=True,
        editable=False,
    )

    def get_account_owner(self):
        return str(self.account.owner)

    def is_transfer(self):
        return bool(self.destination_account)

    @db_transaction.atomic
    def chain_update_balance(self, *args, **kwargs):
        """
        Update balance of all transactions performed after this transaction.
        This instance functions as a manager, calling 'update_balance' on transactions.
        """
        universe = self.account.transaction_set.filter(
            models.Q(timestamp__gt=self.timestamp)
            | (models.Q(timestamp=self.timestamp) & models.Q(created__gt=self.created)),
        )

        updating = self.update_balance()
        super().save(*args, **kwargs)
        previous_balance = self.balance
        for transaction in universe.reverse():
            if not updating:
                return
            updating = transaction.update_balance(previous_balance=previous_balance)
            transaction.save(*args, update_balance=False, **kwargs)
            previous_balance = transaction.balance

    def update_balance(
        self,
        *,
        previous_balance: float | None = None,
        previous_transaction: Optional["Transaction"] = None,
        skip_check: bool = False,
    ) -> bool:
        """
        Update the balance of this instance. Does not write to database.

        Args:
            previous_balance (float, optional):
                Uses this value to calculate balance, if provided.
            previous_transaction (Optional['Transaction']):
                Uses the balance of this transaction to calculate balance, if provided.
            skip_check (bool, optional):
                Don't check if the balance has changed. Defaults to False.
        Returns:
            Returns if the balance has changed.
            If skip_check is set to True, returns True.
        """
        if previous_balance is not None:
            self.balance = previous_balance
        elif previous_transaction is not None:
            self.balance = previous_transaction.balance
        else:
            previous_transaction = self.account.transaction_set.filter(
                models.Q(timestamp__lte=self.timestamp)
                & models.Q(created__lt=self.created),
            ).first()
            if previous_transaction is not None:
                self.balance = previous_transaction.balance
            else:
                self.balance = self.account.initial_balance

        self.balance += self.amount

        try:
            old_instance = self.__class__.objects.get(pk=self.pk)
        except self.__class__.DoesNotExist:
            old_instance = None

        return (
            True
            if skip_check or old_instance is None
            else old_instance.balance != self.balance
        )

    def sync_transfer(self, *args, **kwargs):
        if self.destination_account is None:
            return

        if self.transfer_transaction is None:
            self.transfer_transaction = Transaction()

        self.transfer_transaction.amount = -self.amount
        self.transfer_transaction.account = self.destination_account
        self.transfer_transaction.timestamp = self.timestamp
        self.transfer_transaction.title = self.title
        self.transfer_transaction.description = self.description
        self.transfer_transaction.category = self.category
        self.transfer_transaction.destination_account = self.account

        self.transfer_transaction.save(*args, sync_transfer=False, **kwargs)

        self.transfer_transaction.transfer_transaction = self

    @db_transaction.atomic
    def save(  # noqa: PLR0913
        self,
        *args,
        update_balance=True,
        sync_transfer=True,
        force_insert=False,
        force_update=False,
        update_fields=None,
        **kwargs,
    ):
        if force_update or update_fields:
            if update_balance:
                msg = (
                    "Cannot update balance when using 'force_update', or "
                    f"'update_fields'. Received (force_update={force_update}, "
                    f"update_fields={update_fields})."
                )
                raise ValueError(msg)
            super().save(*args, force_insert, force_update, update_fields, **kwargs)

        try:
            old_instance = self.__class__.objects.get(pk=self.pk)
            # TODO Allow change timestamp ->
            #    If moved backwards, continue.
            #    If moved forward, subtract amount starting at old_timestamp
            #       until new timestamp.
            if (
                old_instance.account != self.account
                or old_instance.timestamp != self.timestamp
            ):
                msg = "Cannot change 'account'."
                raise ValueError(msg)
        except self.__class__.DoesNotExist:
            old_instance = None

        if update_balance:
            self.chain_update_balance(*args, **kwargs)

        if sync_transfer and self.destination_account is not None:
            self.sync_transfer(*args, **kwargs)

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-timestamp", "-created"]
        unique_together = ["timestamp", "created"]
