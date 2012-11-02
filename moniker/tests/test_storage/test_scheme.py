from moniker.tests import TestCase
from moniker.storage import get_engine_name


class TestEngineName(TestCase):
    def test_engine_non_dialected(self):
        name = get_engine_name("mysql")
        self.assertEqual(name, "mysql")

    def test_engine_dialacted(self):
        name = get_engine_name("mysql+oursql")
        self.assertEqual(name, "mysql")
