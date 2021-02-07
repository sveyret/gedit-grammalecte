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

from . import errorstore
from .error import GrammalecteError, _GrammalecteResultEntry
from .errorstore import GrammalecteErrorStore


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(errorstore))
    return tests


class TestErrorStore(unittest.TestCase):
    def setUp(self):
        self.store = GrammalecteErrorStore()
        self.begin = self.buildError((0, 0), (0, 5))
        self.multi = self.buildError((2, 51), (4, 2))
        self.before = self.buildError((8, 4), (8, 15))
        self.after = self.buildError((8, 17), (8, 65))
        self.store.add(self.multi)
        self.store.add(self.begin)
        self.store.add(self.after)
        self.store.add(self.before)

    def buildError(self, start, end):
        return GrammalecteError({
            _GrammalecteResultEntry.LINE_START: start[0] + 1,
            _GrammalecteResultEntry.CHAR_START: start[1],
            _GrammalecteResultEntry.LINE_END: end[0] + 1,
            _GrammalecteResultEntry.CHAR_END: end[1],
            _GrammalecteResultEntry.OPTION: "(option)",
            _GrammalecteResultEntry.RULE: None,
            _GrammalecteResultEntry.DESCRIPTION: "(description)",
            _GrammalecteResultEntry.URL: None,
            _GrammalecteResultEntry.SUGGESTIONS: [],
        })

    def test_order(self):
        prev = 0
        for error in self.store:
            line, _ = error.start
            self.assertGreaterEqual(line, prev)
            prev = line

    def test_len(self):
        self.assertEqual(len(self.store), 4)

    def test_search_begin(self):
        self.assertEqual(self.store.search((0, 0)), self.begin)
        self.assertEqual(self.store.search((0, 3)), self.begin)
        self.assertEqual(self.store.search((0, 5)), self.begin)

    def test_search_multi_begin_fail(self):
        self.assertEqual(self.store.search((2, 12)), None)

    def test_search_multi_begin(self):
        self.assertEqual(self.store.search((2, 52)), self.multi)

    def test_search_multi_middle(self):
        self.assertEqual(self.store.search((3, 0)), self.multi)

    def test_search_multi_end(self):
        self.assertEqual(self.store.search((4, 1)), self.multi)

    def test_search_multi_end_fail(self):
        self.assertEqual(self.store.search((4, 5)), None)

    def test_search_before(self):
        self.assertEqual(self.store.search((8, 15)), self.before)

    def test_search_after(self):
        self.assertEqual(self.store.search((8, 17)), self.after)

    def test_search_between(self):
        self.assertEqual(self.store.search((8, 16)), None)


if __name__ == '__main__':
    unittest.main()
