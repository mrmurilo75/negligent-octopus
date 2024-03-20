import pytest
from django.utils import timezone
from faker import Faker

from negligent_octopus.core.models import Account
from negligent_octopus.core.tests.factories import TransactionFactory

faker = Faker()


@pytest.mark.django_db()
class TestAccountTransactionBalance:
    def test_account_balance(self, account: Account):
        balance = account.initial_balance
        for i in range(10):
            balance += i
            TransactionFactory(
                account=account,
                amount=i,
                timestamp=timezone.now(),  # Make sure they are in order
            )
        assert account.balance == balance

    def test_account_initial_balance_change(self, account: Account):
        raise NotImplementedError

    def test_transaction_added_last(self, account: Account):
        raise NotImplementedError

    def test_transaction_added_first(self, account: Account):
        raise NotImplementedError

    def test_transaction_added_middle(self, account: Account):
        raise NotImplementedError

    def test_transaction_change_amount(self, account: Account):
        raise NotImplementedError
