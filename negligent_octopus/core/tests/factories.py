import factory
from factory.django import DjangoModelFactory

from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Transaction


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    owner = factory.SubFactory("negligent_octopus.users.tests.factories.UserFactory")
    name = factory.Faker("word")
    initial_balance = factory.Faker("random_number", digits=2)


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    account = factory.SubFactory(AccountFactory)
    amount = factory.Faker("random_number", digits=2)
    title = factory.Faker("word")
