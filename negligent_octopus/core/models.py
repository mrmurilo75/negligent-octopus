from django.db import models
from django.utils import timezone
from model_utils.models import SoftDeletableModel
from model_utils.models import TimeStampedModel

from negligent_octopus.users.models import User


class Account(TimeStampedModel, SoftDeletableModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    balance = models.FloatField(default=0.0, editable=False)

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
