import pytest

from negligent_octopus.core.tests.factories import AccountFactory
from negligent_octopus.core.tests.factories import TransactionFactory


@pytest.fixture()
def account():
    return AccountFactory()


@pytest.fixture()
def transaction():
    return TransactionFactory()
