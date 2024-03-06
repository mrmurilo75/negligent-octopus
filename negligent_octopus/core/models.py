from datetime import datetime
from django.db import models
from model_utils.models import SoftDeletableModel
from model_utils.models import TimeStampedModel


from negligent_octopus.users.models import User


class Account(TimeStampedModel, SoftDeletableModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    calculated_balance = models.FloatField(default=0.0, editable=False)
    calculated_at = models.DateTimeField(default=datetime.now) # Uses datetime.datetime instead of auto_add_now because the latter uses django.timezone

    @propery
    def balance(self):
        # Set calculated_at to now (now_at)
        # Get relevant transaction (Get creation or modified after now_at)
        # For each do a running sum, taking in consideration delta of all modifications after now_at
            # Check for any modification on is_removed and consider into the delta (just negative of last calculation - is this correct?)
        # Update calculated_balance and return it
        # #IMPROVE : Evaluate using atomic or another techinique to prevent conflicts on reading and updating

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["-modified", "name"]


class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.FloatField()
    date = models.DateField(default=timezone.now)
    title = models.CharField(max_length=127)
    description = models.TextField(blank=True)

    def get_account_owner(self):
        return str(self.account.owner)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["date", "-modified"]
