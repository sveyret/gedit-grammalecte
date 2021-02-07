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

from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union, TYPE_CHECKING

from .avltree import AvlTree
from .error import GrammalecteError

ErrorPosition = Tuple[int, int]
if TYPE_CHECKING:
    GErrorAvlTree = AvlTree[GrammalecteError]
else:
    GErrorAvlTree = AvlTree


class GrammalecteErrorStore(GErrorAvlTree):
    """
    An AVL tree storing the errors.

    Errors are sorted on their line and offset numbers.

    :Example:

    >>> from .error import _GrammalecteResultEntry
    >>> def buildError(pos): return GrammalecteError({ \
_GrammalecteResultEntry.LINE_START: pos[0] + 1, \
_GrammalecteResultEntry.CHAR_START: pos[1], \
_GrammalecteResultEntry.LINE_END: pos[0] + 1, \
_GrammalecteResultEntry.CHAR_END: pos[1] + 1, \
_GrammalecteResultEntry.OPTION: "O", \
_GrammalecteResultEntry.SUGGESTIONS: [] })

    >>> store = GrammalecteErrorStore()
    >>> store.add(buildError((12,1)))
    >>> store.add(buildError((2,1)))
    >>> store.add(buildError((1,2)))
    >>> store.add(buildError((5,16)))
    >>> store.add(buildError((5,1)))

    >>> len(store)
    5
    >>> store.height
    2
    >>> print(store)
    Analysis error [1,2:1,3]: O, Analysis error [2,1:2,2]: O, \
Analysis error [5,1:5,2]: O, Analysis error [5,16:5,17]: O, \
Analysis error [12,1:12,2]: O
    """

    def __init__(self) -> None:
        """
        Create the store.
        """
        AvlTree.__init__(self, self.__compare)

    def add_all(self, errors: Iterable[GrammalecteError]) -> None:
        """
        Add all elements of the iterable to the store.

        :param errors: The errors to add to store.
        """
        for error in errors:
            self.add(error)

    def search(self, data: Union[ErrorPosition, Union[GrammalecteError, Callable[[GrammalecteError], int]]]) -> Optional[GrammalecteError]:  # type: ignore
        """
        Search the error at given position if data is tuple. Otherwise, simply
        call super function.

        :param data: the position of the error to search (line#, char#), the
        error or the comparison function.
        :return: the found error or None if none found.
        """
        if type(data) is tuple:
            return AvlTree.search(self,
                                  lambda e: self.__searchComp(e, data))  # type: ignore
        else:
            return AvlTree.search(self, data)  # type: ignore

    def __compare(self, lerror: GrammalecteError, rerror: GrammalecteError) -> int:
        """
        Compare two errors.

        The comparison is made on start line and offset numbers.

        :param lerror: the left error.
        :param rerror: the right error.
        :return: negative value if lerror is lower, positive if lerror is
                bigger, 0 if errors are equal.
        """
        lline, loffset = lerror.start
        rline, roffset = rerror.start
        diff = lline - rline
        return diff if diff != 0 else loffset - roffset

    def __searchComp(self, error: GrammalecteError, position: ErrorPosition) -> int:
        """
        Test if the error is at the given position.

        This will be true if the position is between start and end positions of
        the error. If so, the function will return 0, otherwise, it will return
        the difference between error start coordinates and given position.

        :param error: the error to test.
        :param position: the position to test (line#, char#).
        :return: negative value if error is too low, positive if too big, 0 if
        error matchs.
        """
        sline, soffset = error.start
        eline, eoffset = error.end
        pline, poffset = position
        if (sline < pline and pline < eline) or \
                (sline != eline and sline == pline and soffset <= poffset) or \
                (sline != eline and pline == eline and poffset <= eoffset) or \
                (sline == eline and sline == pline and
                 soffset <= poffset and poffset <= eoffset):
            return 0
        else:
            diff = sline - pline
            return diff if diff != 0 else soffset - poffset
