from datetime import timedelta

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

    def test_transaction_balance(self, account: Account):
        balance = account.initial_balance
        for i in range(10):
            TransactionFactory(
                account=account,
                amount=i,
                timestamp=timezone.now(),  # Make sure they are in order
            )
        for i, transaction in zip(
            range(10),
            account.transaction_set.all().reverse(),
            strict=False,
        ):
            balance += i
            assert transaction.balance == balance

    def test_account_initial_balance_change(self, account: Account):
        balance = account.initial_balance
        for i in range(10):
            TransactionFactory(
                account=account,
                amount=i,
                timestamp=timezone.now(),  # Make sure they are in order
            )
        account.initial_balance += 1
        account.save()

        for i, transaction in zip(
            range(10),
            account.transaction_set.all().reverse(),
            strict=False,
        ):
            balance += i
            assert transaction.balance == balance + 1

    def test_transaction_added_before(self, account: Account):
        now = timezone.now()
        TransactionFactory(
            account=account,
            amount=10,
            timestamp=now,
        )
        transaction = TransactionFactory(
            account=account,
            amount=10,
            timestamp=now,
        )
        old_balance = account.balance

        transaction_before = TransactionFactory(
            account=account,
            amount=11,
            timestamp=now - timedelta(minutes=1),
        )
        TransactionFactory(
            account=account,
            amount=11,
            timestamp=now - timedelta(minutes=1),
        )

        assert account.transaction_set.first().pk == transaction.pk
        assert account.transaction_set.last().pk == transaction_before.pk

        assert old_balance == account.initial_balance + 20
        assert account.balance == old_balance + 22

    def test_transaction_added_middle(self, account: Account):
        now = timezone.now()
        first_transaction = TransactionFactory(
            account=account,
            amount=1,
            timestamp=now,
        )
        third_transaction = TransactionFactory(
            account=account,
            amount=100,
            timestamp=now + timedelta(minutes=2),
        )
        TransactionFactory(
            account=account,
            amount=10,
            timestamp=now + timedelta(minutes=1),
        )

        # Reload instances
        first_transaction = account.transaction_set.get(pk=first_transaction.pk)
        third_transaction = account.transaction_set.get(pk=third_transaction.pk)

        assert first_transaction.balance == account.initial_balance + 1
        assert third_transaction.balance == account.initial_balance + 1 + 10 + 100

    def test_transaction_change_amount(self, account: Account):
        now = timezone.now()
        first_transaction = TransactionFactory(
            account=account,
            amount=1,
            timestamp=now,
        )
        second_transaction = TransactionFactory(
            account=account,
            amount=10,
            timestamp=now + timedelta(minutes=1),
        )
        third_transaction = TransactionFactory(
            account=account,
            amount=100,
            timestamp=now + timedelta(minutes=2),
        )
        second_transaction.amount += 10
        second_transaction.save()

        # Reload instances
        first_transaction = account.transaction_set.get(pk=first_transaction.pk)
        third_transaction = account.transaction_set.get(pk=third_transaction.pk)

        assert first_transaction.balance == account.initial_balance + 1
        assert second_transaction.balance == account.initial_balance + 1 + 20
        assert third_transaction.balance == account.initial_balance + 1 + 20 + 100
