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

    def delete(self, *args, **kwargs):
        # TODO Delete all transfers before continuing
        return super().delete(*args, **kwargs)

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
    destination_account_name = models.CharField(max_length=255, blank=True)
    destination_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        # TODO: Set account name to the name, and set this to none
        # '--> Same as deleting transaction without deleting transfer
        related_name="transfer_set",
        blank=True,
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

    def after(self, using=None):
        """
        Returns:
            All transactions in this account that happened after this.
        """
        universe = self.account.transaction_set
        if using is not None:
            universe = universe.using(using)

        return universe.filter(
            models.Q(timestamp__gt=self.timestamp)
            | (models.Q(timestamp=self.timestamp) & models.Q(created__gt=self.created)),
        )

    def next(self, using=None):
        """
        Returns:
            The transaction in this account that happened right after this.
        """
        return self.after(using=using).last()

    def before(self, using=None):
        """
        Returns:
            All transactions in this account that happened after this.
        """
        universe = self.account.transaction_set
        if using is not None:
            universe = universe.using(using)

        return universe.filter(
            models.Q(timestamp__lt=self.timestamp)
            | (models.Q(timestamp=self.timestamp) & models.Q(created__lt=self.created)),
        )

    def previous(self, using=None):
        """
        Returns:
            The transaction in this account that happened right after this.
        """
        return self.before(using=using).first()

    def get_account_owner(self):
        return str(self.account.owner)

    def is_transfer(self):
        return bool(self.destination_account)

    @db_transaction.atomic
    def chain_update_balance(self, start_transaction, *args, **kwargs):
        """
        Update balance of all transactions performed after this transaction.
        This instance functions as a manager, calling 'update_balance' on transactions.
        """
        using = kwargs.get("using")
        kwargs["sync_transfer"] = False
        kwargs["update_balance"] = False

        universe = start_transaction.after(using=using)

        def inner_update_balance(transaction, previous_balance):
            transaction.update_balance(
                previous_balance=previous_balance,
                using=using,
                commit=True,
            )
            return transaction.balance

        previous_balance = inner_update_balance(start_transaction, None)

        for transaction in universe.reverse():
            previous_balance = inner_update_balance(
                self if transaction.pk == self.pk else transaction,
                previous_balance,
            )
            # 'universe' qs returns a new instance of this transaction
            # which is saved but overriden if we later call save on this transaction.

    def update_balance(
        self,
        *,
        previous_balance: float | None = None,
        using=None,
        commit=False,
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
            commit (bool, optional):
                Whether to save the updated balance. If it is an update operation,
                it saves only the balance. Defaults to False.

        Returns:
            Returns if the balance has changed.
            If skip_check is set to True, returns True.
        """
        if previous_balance is not None:
            self.balance = previous_balance
        else:
            previous_transaction = self.previous(using=using)
            if previous_transaction is not None:
                self.balance = previous_transaction.balance
            else:
                self.balance = self.account.initial_balance

        self.balance += self.amount

        try:
            manager = self.__class__.objects
            if using is not None:
                manager = manager.using(using)
            old_instance = manager.get(pk=self.pk)
        except self.__class__.DoesNotExist:
            old_instance = None

        if commit:
            kwargs = {
                "using": using,
                "update_balance": False,
                "sync_transfer": False,
            }
            if old_instance is not None:
                kwargs["update_fields"] = ("balance",)
            self.save(**kwargs)

        return old_instance is None or old_instance.balance != self.balance

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

        for kw in ("force_insert", "force_update", "update_fields"):
            kwargs.pop(kw, None)
        self.transfer_transaction.save(*args, sync_transfer=False, **kwargs)

        self.transfer_transaction.transfer_transaction = self

    @db_transaction.atomic
    def save(
        self,
        *args,
        update_balance=True,
        sync_transfer=True,
        using=None,
        **kwargs,
    ):
        try:
            manager = self.__class__.objects
            if using is not None:
                manager = manager.using(using)
            old_instance = manager.get(pk=self.pk)
            # TODO Change recalculating balance on transactions to a lazy strategy
            # TODO Allow change timestamp ->
            #    If moved backwards, continue.
            #    If moved forward, subtract amount starting at old_timestamp
            #       until new timestamp.
            msg = None
            if old_instance.account != self.account:
                msg = "Cannot change 'account'."
            if (
                old_instance.destination_account is not None
                and old_instance.destination_account != self.destination_account
                and not (  # Allow remove destination_account if "_name is added
                    self.destination_account is None
                    and self.destination_account_name is not None
                )
            ):
                msg = "Cannot change 'destination_account'."
                raise ValueError(msg)
        except self.__class__.DoesNotExist:
            old_instance = None

        start_transaction = self
        if (
            old_instance is not None
            and self.timestamp > old_instance.timestamp
            and self.pk != self.account.transaction_set.first()
        ):
            start_transaction = old_instance.next()

        super().save(*args, **kwargs)

        kwargs.pop(
            "force_insert",
            None,
        )  # We might call super().save again, so we cannot force insert

        if update_balance:
            self.chain_update_balance(start_transaction, *args, **kwargs)

        if sync_transfer and self.destination_account is not None:
            self.sync_transfer(*args, **kwargs)

        super().save(*args, **kwargs)

    @db_transaction.atomic
    def delete(self, *args, delete_transfer=True, using=None, **kwargs):
        transfer = self.transfer_transaction
        if delete_transfer and transfer is not None:
            transfer.destination_account_name = str(transfer.destination_account)
            transfer.destination_account = None

        self.destination_account = None
        self.transfer_transaction = None
        self.amount = 0
        self.save(using=using)

        if delete_transfer and transfer is not None:
            transfer.delete(*args, delete_transfer=False, using=using, **kwargs)

        super().delete(*args, using=using, **kwargs)

    def __str__(self):
        return str(self.title)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-timestamp", "-created"]
        unique_together = ["timestamp", "created"]
