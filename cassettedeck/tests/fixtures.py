import pytest
import os

from cassettedeck.deck import CassetteDeck


@pytest.fixture(scope='function')
def ctd(caplog):
    yield CassetteDeck()


@pytest.fixture(scope='function')
def ctd_custom_dir():
    cassettes_folder = os.path.join(os.path.curdir, f'stored_requests')
    yield CassetteDeck(cassette_library_dir=cassettes_folder)
