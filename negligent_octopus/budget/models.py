from django.db import models
from model_utils.models import TimeStampedModel

from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Transaction
from negligent_octopus.users.models import User


class LoadActivo(TimeStampedModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    load = models.FileField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE)


class ImportedTransaction(Transaction):
    pass
