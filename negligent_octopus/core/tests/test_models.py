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
    def get_transaction_stage(self, count=5):
        account = AccountFactory()
        return [
            TransactionFactory(
                account=account,
                title=i,
                timestamp=timezone.now(),  # Make sure they are in order
            )
            for i in range(count)
        ]

    def _move_backwards_to_first(self):
        transactions = self.get_transaction_stage()
        transactions[1].title = "new 0"
        transactions[1].timestamp = transactions[0].timestamp - timedelta(seconds=1)
        transactions[1].save()
        transactions[0], transactions[1] = transactions[1], transactions[0]
        return transactions

    def _move_forward(self):
        transactions = self.get_transaction_stage()
        transactions[0].title = "new 2"
        transactions[0].timestamp = transactions[3].timestamp
        # Same timestamp but created earlier
        transactions[0].save()
        return transactions[1:3] + [transactions[0]] + transactions[3:]

    def _insert_middle(self):
        transactions = self.get_transaction_stage()
        new_transaction = TransactionFactory(
            account=transactions[0].account,
            title="new 3",
            timestamp=transactions[2].timestamp,
            # Same timestamp but created after
        )
        return transactions[:3] + [new_transaction] + transactions[3:]

    def _delete_middle(self):
        transactions = self.get_transaction_stage()
        transactions[3].delete()
        return transactions[:3] + transactions[4:]

    def _insert_transfer_middle(self):
        originals = self.get_transaction_stage()
        destination_account = AccountFactory(name="destination")
        destinations = [
            TransactionFactory(
                account=destination_account,
                title=og.title,
                timestamp=og.timestamp,
            )
            for og in originals
        ]
        new_transaction = TransactionFactory(
            account=originals[0].account,
            title="new 3",
            timestamp=originals[2].timestamp,
            # Same timestamp but created after
            destination_account=destination_account,
        )
        originals = originals[:3] + [new_transaction] + originals[3:]
        destinations = (
            destinations[:3] + [new_transaction.transfer_transaction] + destinations[3:]
        )
        return originals, destinations, new_transaction

    def _move_transfer_backwards_to_first(self):
        originals, destinations, transfer = self._insert_transfer_middle()
        transfer.title = "new 0"
        transfer.timestamp = originals[0].timestamp - timedelta(seconds=1)
        transfer.save()
        originals = [transfer] + [t for t in originals if t.title != transfer.title]
        destinations = [transfer.transfer_transaction] + [
            t for t in destinations if t.title != transfer.title
        ]

        return originals, destinations

    def _move_transfer_forward(self):
        originals, destinations, transfer = self._insert_transfer_middle()
        transfer.title = "new 2"
        transfer.timestamp = originals[-2].timestamp
        # Same timestamp but created after
        transfer.save()
        originals = [t for t in originals[:-1] if t.title != transfer.title] + [
            transfer,
            originals[-1],
        ]
        destinations = [t for t in destinations[:-1] if t.title != transfer.title] + [
            transfer.transfer_transaction,
            destinations[-1],
        ]
        return originals, destinations

    def _delete_transfer(self):
        originals, destinations, transfer = self._insert_transfer_middle()
        transfer.delete()
        originals = [t for t in originals if t.title != transfer.title]
        destinations = [t for t in destinations if t.title != transfer.title]
        return originals, destinations

    def _test(self, test_function):
        test_function(self.get_transaction_stage())
        test_function(self._move_backwards_to_first())
        test_function(self._move_forward())
        test_function(self._insert_middle())
        test_function(self._delete_middle())

        originals, destinations, _t = self._insert_transfer_middle()
        test_function(originals)
        test_function(destinations)
        originals, destinations = self._move_transfer_backwards_to_first()
        test_function(originals)
        test_function(destinations)
        originals, destinations = self._move_transfer_forward()
        test_function(originals)
        test_function(destinations)
        originals, destinations = self._delete_transfer()
        test_function(originals)
        test_function(destinations)

    def test_create(self, account: Account):
        value = 1.1
        transaction = TransactionFactory(
            account=account,
            amount=value,
        )
        assert transaction.balance == account.initial_balance + value
        assert not transaction.is_transfer

    def test_sequence(self):
        def inner_test_sequence(transactions):
            acc = transactions[0].account
            rtransactions = transactions[::-1]
            length = len(rtransactions)
            for i in range(length):
                rtransactions[i] = Transaction.objects.get(pk=rtransactions[i].pk)

            try:
                assert list(acc.transaction_set.all()) == rtransactions

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

        self._test(inner_test_sequence)

    def test_balance(self):
        def inner_test_balance(transactions):
            try:
                previous_balance = transactions[0].account.initial_balance
                for transaction in transactions:
                    assert transaction.balance == (
                        previous_balance + transaction.amount
                    )
                    previous_balance = transaction.balance
            except AssertionError:
                logger.warning(
                    json.dumps(
                        {t.title: t.balance for t in transactions},
                        indent=4,
                    ),
                )
                raise

        self._test(inner_test_balance)
