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

from . import avltree
from .avltree import AvlTree


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(avltree))
    return tests


class TestAvlTree(unittest.TestCase):
    def setUp(self):
        self.tree = AvlTree(self.compare, 51)
        self.tree.add(-12)
        self.tree.add(25)
        self.tree.add(69)
        self.tree.add(-2)
        self.tree.add(2)

    def compare(self, left, right):
        return left - right

    def test_order(self):
        prev = -127
        for element in self.tree:
            self.assertGreaterEqual(element, prev)
            prev = element

    def test_len(self):
        self.assertEqual(len(self.tree), 6)


if __name__ == '__main__':
    unittest.main()
