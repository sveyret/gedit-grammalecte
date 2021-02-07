# This file is part of gedit-grammalecte.
#
# gedit-grammalecte is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# gedit-grammalecte is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# gedit-grammalecte. If not, see <http://www.gnu.org/licenses/>.

import doctest
import unittest

from . import config
from .config import DictConfig


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(config))
    return tests


class TestDictConfig(unittest.TestCase):
    def setUp(self):
        self.defaultConfig = DictConfig({"key0": "value0",
                                         "key1": "invisible"})
        self.config = DictConfig({"key1": "value1",
                                  "key2": {"key21": ["value21a", "value21b"], "key22": "value22"},
                                  "key3": "value3"}, self.defaultConfig)

    def test_get_simple_value(self):
        self.assertEqual(self.config.get_value("key3"), "value3")

    def test_get_complex_value(self):
        self.assertEqual(self.config.get_value("key2/key21/1"), "value21b")

    def test_get_default_value(self):
        self.assertEqual(self.config.get_value("key0"), "value0")

    def test_set_simple_value(self):
        self.config.set_value("key1", "newValue1")
        self.assertEqual(self.config.get_value("key1"), "newValue1")
        self.assertEqual(self.defaultConfig.get_value("key1"), "invisible")

    def test_set_complex_value(self):
        self.config.set_value("key2/key21/0", {"a": "newValuea",
                                               "b": "newValueb"})
        self.assertEqual(self.config.get_value("key2/key21/0/b"), "newValueb")

    def test_set_default_value(self):
        self.config.set_value("key1", "newValue1", 1)
        self.assertEqual(self.config.get_value("key1"), "value1")
        self.assertEqual(self.defaultConfig.get_value("key1"), "newValue1")

    def test_create_value(self):
        self.config.set_value("key4/hello", "world")
        self.assertEqual(self.config.get_value("key4/hello"), "world")


if __name__ == '__main__':
    unittest.main()
