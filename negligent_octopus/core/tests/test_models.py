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
class TestAccount:
    def test_create(self):
        initial = 1.1
        acc = AccountFactory(
            name="Test",
            initial_balance=initial,
        )
        assert acc.name == "Test"
        assert acc.initial_balance == initial
        assert acc.balance == initial

    def test_add_transactions(self, account: Account):
        balance = account.initial_balance
        for i, value in enumerate(range(5), 1):
            balance += value
            TransactionFactory(
                account=account,
                amount=value,
                timestamp=timezone.now(),  # Make sure they are in order
            )
            assert account.balance == balance
            assert account.transaction_set.count() == i

    def test_change_initial_balance(self, account: Account):
        for value in range(5):
            TransactionFactory(
                account=account,
                amount=value,
                timestamp=timezone.now(),  # Make sure they are in order
            )
        old_balance = account.balance
        account.initial_balance += 1.1
        account.save()

        account = Account.objects.get(pk=account.pk)

        assert account.balance == old_balance + 1.1

    def test_delete(self, account: Account):
        account.delete()

        with pytest.raises(Account.DoesNotExist):
            Account.objects.get(pk=account.pk)


@pytest.mark.django_db()
class TestTransaction:
    def test_create(self, account: Account):
        value = 1.1
        transaction = TransactionFactory(
            account=account,
            amount=value,
        )
        assert transaction.balance == account.initial_balance + value
        assert not transaction.is_transfer

    def test_sequence(self, account: Account):
        def inner_test_sequence(first, middle, last):
            first = Transaction.objects.get(pk=first.pk)
            middle = Transaction.objects.get(pk=middle.pk)
            last = Transaction.objects.get(pk=last.pk)

            assert list(account.transaction_set.all()) == [
                last,
                middle,
                first,
            ]

            assert first.next() == middle
            assert middle.previous() == first

            assert list(first.after()) == [
                last,
                middle,
            ]
            assert list(last.before()) == [
                middle,
                first,
            ]

            assert first.previous() is None
            assert last.next() is None

            assert len(first.before()) == 0
            assert len(last.after()) == 0

        transactions = [
            TransactionFactory(
                account=account,
                title=title,
                timestamp=timezone.now(),  # Make sure they are in order
            )
            for title in ("first", "middle", "last")
        ]
        inner_test_sequence(*transactions)

        # Move middle backward by timestamp
        transactions[1].title = "new_first"
        transactions[1].timestamp = transactions[0].timestamp - timedelta(seconds=1)
        transactions[1].save()
        transactions[0], transactions[1] = transactions[1], transactions[0]
        inner_test_sequence(*transactions)

        # Move first forward by timestamp
        transactions[0].title = "new_middle"
        transactions[0].timestamp = transactions[2].timestamp
        # Same timestamp but created earlier
        transactions[0].save()
        transactions[0], transactions[1] = transactions[1], transactions[0]
        inner_test_sequence(*transactions)

        # TODO Insert transaction between 1 and 2

        # TODO Delete a transaction

    def test_balance(self, account: Account):
        def inner_test_balance(first, middle, last):
            first = Transaction.objects.get(pk=first.pk)
            middle = Transaction.objects.get(pk=middle.pk)
            last = Transaction.objects.get(pk=last.pk)

            assert first.balance == account.initial_balance + first.amount
            assert middle.balance == first.balance + middle.amount
            assert last.balance == middle.balance + last.amount

        transactions = []
        values = [(value + value / 10) for value in range(3)]
        for title, value in enumerate(values):
            transactions.append(
                TransactionFactory(
                    account=account,
                    title=title,
                    amount=value,
                    timestamp=timezone.now(),  # Make sure they are in order
                ),
            )
        inner_test_balance(*transactions)

        # Move middle backward by timestamp
        transactions[1].title = "new_0"
        transactions[1].timestamp = transactions[0].timestamp - timedelta(seconds=1)
        transactions[1].save()
        transactions[0], transactions[1] = transactions[1], transactions[0]
        inner_test_balance(*transactions)

        # Move first forward by timestamp
        transactions[0].title = "new_1"
        transactions[0].timestamp = transactions[2].timestamp
        # Same timestamp but created earlier
        transactions[0].save()
        transactions[0], transactions[1] = transactions[1], transactions[0]
        inner_test_balance(*transactions)

        # Change amount
        transactions[0].amount += 1.1
        transactions[0].save()
        inner_test_balance(*transactions)

        # TODO Insert transaction between 1 and 2

        # TODO Delete a transaction

    def test_transfer(self, account: Account):
        raise NotImplementedError


@pytest.mark.django_db()
def test_transaction_transfer(account: Account):
    transaction = TransactionFactory(
        account=account,
        amount=10.10,
        timestamp=timezone.now(),
    )
    transaction.destination_account = AccountFactory()
    transaction.save()
    transaction.transfer_transaction.save()

    assert transaction.transfer_transaction.amount == -transaction.amount
    assert transaction.transfer_transaction.account == transaction.destination_account
    assert (
        transaction.destination_account.balance
        == transaction.destination_account.initial_balance - transaction.amount
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

    def test_transaction_timestamp_forward(self, account: Account):
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
        second_transaction.timestamp = now + timedelta(minutes=3)
        second_transaction.save()

        # Reload instances
        first_transaction = account.transaction_set.get(pk=first_transaction.pk)
        third_transaction = account.transaction_set.get(pk=third_transaction.pk)

        assert first_transaction.balance == account.initial_balance + 1
        assert third_transaction.balance == account.initial_balance + 1 + 100
        assert second_transaction.balance == account.initial_balance + 1 + 10 + 100

        assert second_transaction.next() is None
        assert second_transaction.previous() == third_transaction
