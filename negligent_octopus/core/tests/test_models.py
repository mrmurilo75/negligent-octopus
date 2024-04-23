# ruff: noqa: F811
import json
import logging
from datetime import timedelta

import pytest
from django.utils import timezone
from faker import Faker

from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Transaction
from negligent_octopus.core.tests.factories import AccountFactory
from negligent_octopus.core.tests.factories import TransactionFactory
from negligent_octopus.core.tests.fixtures import account  # noqa: F401

logger = logging.getLogger(__name__)

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
    def _move_backwards_to_first(self, transactions):
        transactions[1].title = "new 0"
        transactions[1].timestamp = transactions[0].timestamp - timedelta(seconds=1)
        transactions[1].save()
        transactions[0], transactions[1] = transactions[1], transactions[0]
        return transactions

    def _move_forward(self, transactions):
        transactions[0].title = "new 2"
        transactions[0].timestamp = transactions[3].timestamp
        # Same timestamp but created earlier
        transactions[0].save()
        return transactions[1:3] + [transactions[0]] + transactions[3:]

    def _insert_middle(self, account, transactions):
        new_transaction = TransactionFactory(
            account=account,
            title="new 3",
            timestamp=transactions[2].timestamp,
            # Same timestamp but created after
        )
        return transactions[:3] + [new_transaction] + transactions[3:]

    def _delete_middle(self, transactions):
        transactions[3].delete()
        return transactions[:3] + transactions[4:]

    def test_create(self, account: Account):
        value = 1.1
        transaction = TransactionFactory(
            account=account,
            amount=value,
        )
        assert transaction.balance == account.initial_balance + value
        assert not transaction.is_transfer

    def test_sequence(self, account: Account):
        def inner_test_sequence(transactions):
            rtransactions = transactions[::-1]
            length = len(rtransactions)
            for i in range(length):
                rtransactions[i] = Transaction.objects.get(pk=rtransactions[i].pk)

            try:
                assert list(account.transaction_set.all()) == rtransactions

                assert rtransactions[0].next() is None
                assert rtransactions[length - 1].previous() is None

                for i in range(1, length):
                    assert rtransactions[i].next() == rtransactions[i - 1]
                    assert rtransactions[i - 1].previous() == rtransactions[i]

                for i in range(length):
                    assert list(rtransactions[i].after()) == rtransactions[:i]
                    assert list(rtransactions[i].before()) == rtransactions[i + 1 :]
            except AssertionError:
                logger.warning(
                    json.dumps(
                        {t.title: str(t.timestamp) for t in transactions},
                        indent=4,
                    ),
                )
                raise

        def get_transaction_stage():
            account.transaction_set.all().delete()
            return [
                TransactionFactory(
                    account=account,
                    title=i,
                    timestamp=timezone.now(),  # Make sure they are in order
                )
                for i in range(5)
            ]

        inner_test_sequence(get_transaction_stage())
        inner_test_sequence(self._move_backwards_to_first(get_transaction_stage()))
        inner_test_sequence(self._move_forward(get_transaction_stage()))
        inner_test_sequence(self._insert_middle(account, get_transaction_stage()))
        inner_test_sequence(self._delete_middle(get_transaction_stage()))

    def test_balance(self, account: Account):
        def inner_test_balance(transactions):
            previous_balance = account.initial_balance
            for transaction in transactions:
                assert transaction.balance == previous_balance + transaction.amount
                previous_balance = transaction.balance

        values = [(value + value / 10) for value in range(5)]

        def get_transaction_stage():
            account.transaction_set.all().delete()
            return [
                TransactionFactory(
                    account=account,
                    title=title,
                    amount=value,
                    timestamp=timezone.now(),  # Make sure they are in order
                )
                for title, value in enumerate(values)
            ]

        inner_test_balance(get_transaction_stage())
        inner_test_balance(self._move_backwards_to_first(get_transaction_stage()))
        inner_test_balance(self._move_forward(get_transaction_stage()))
        inner_test_balance(self._insert_middle(account, get_transaction_stage()))
        inner_test_balance(self._delete_middle(get_transaction_stage()))

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
