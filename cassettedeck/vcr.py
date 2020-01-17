import inspect
import os
from contextlib import contextmanager
from unittest import TestCase

from cassettedeck import CassetteDeck


@contextmanager
def vcr(test_case: TestCase):
    """
    Test utility which allows cassettes to be stored with a unique name near their point of use.
    """
    test_file = inspect.getfile(type(test_case))
    library = os.path.join(os.path.dirname(test_file), "cassettes")
    my_vcr = CassetteDeck(cassette_library_dir=library, ignore_localhost=True)
    with my_vcr.use_cassette(f"{test_case.id()}.yaml", mode="once") as cassette:
        yield cassette
