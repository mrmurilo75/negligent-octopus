# ruff: noqa: F811
from datetime import timedelta

import pytest
from django.utils import timezone
from faker import Faker

from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Transaction
from negligent_octopus.core.tests.factories import AccountFactory
from negligent_octopus.core.tests.factories import TransactionFactory
from negligent_octopus.core.tests.fixtures import account  # noqa: F401

faker = Faker()


@pytest.mark.django_db()
def test_transaction_transfer(account: Account):
    transaction = TransactionFactory(
        account=account,
        amount=10.10,
        timestamp=timezone.now(),
    )
    transaction.destination_account = AccountFactory()
    transaction.save()

    assert transaction.transfer_transaction.amount == -transaction.amount
    assert transaction.transfer_transaction.account == transaction.destination_account
    assert (
        transaction.destination_account.balance
        == transaction.destination_account.initial_balance - transaction.balance
    )
    assert transaction.transfer_transaction.timestamp == transaction.timestamp
    assert transaction.transfer_transaction.title == transaction.title
    assert transaction.transfer_transaction.description == transaction.description
    assert transaction.transfer_transaction.category == transaction.category
    assert transaction.transfer_transaction.destination_account == transaction.account
    assert transaction.transfer_transaction.transfer_transaction == transaction


@pytest.mark.django_db()
def test_transaction_transfer_delete(account: Account):
    transaction = TransactionFactory(
        account=account,
        amount=10.10,
        timestamp=timezone.now(),
    )
    destination_account = AccountFactory()
    transaction.destination_account = destination_account
    transaction.save()

    transaction_pk = transaction.pk
    transfer_pk = transaction.transfer_transaction.pk

    transaction.delete(delete_transfer=True)

    with pytest.raises(Transaction.DoesNotExist):
        Transaction.objects.get(pk=transaction_pk)

    with pytest.raises(Transaction.DoesNotExist):
        Transaction.objects.get(pk=transfer_pk)

    assert account.balance == account.initial_balance
    assert destination_account.balance == destination_account.initial_balance


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

    def test_transaction_delete(self, account: Account):
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
        second_pk = second_transaction.pk
        second_transaction.delete()

        # Reload instances
        first_transaction = account.transaction_set.get(pk=first_transaction.pk)
        third_transaction = account.transaction_set.get(pk=third_transaction.pk)

        assert first_transaction.balance == account.initial_balance + 1
        with pytest.raises(Transaction.DoesNotExist):
            account.transaction_set.get(pk=second_pk)

        assert third_transaction.balance == account.initial_balance + 1 + 100
