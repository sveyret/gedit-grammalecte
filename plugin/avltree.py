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

from typing import Any, Callable, Generic, Iterator, Optional, TypeVar, Union

T = TypeVar('T')


class _BNode(Generic[T]):
    """
    A node of a binary tree.

    A node contains a value, a parent, a left and an right child. The parent
    node may be null (root node).

    Note that node removal is not implemented.
    """

    def __init__(self, element: T) -> None:
        """
        Create the node under the given parent.

        :param element: the element to store in this node.
        """
        self.__element: T = element
        self.__parent: Optional[_BNode] = None
        self.__left: Optional[_BNode] = None
        self.__right: Optional[_BNode] = None
        self.__height: int = -1

    def saw_children(self) -> None:
        """
        Saw (remove) the children from the tree starting at this node.
        """
        if self.__left is not None:
            self.__left.saw_children()
            self.__left.__parent = None
            self.__left = None
        if self.__right is not None:
            self.__right.saw_children()
            self.__right.__parent = None
            self.__right = None

    def __iter__(self) -> Iterator[T]:
        """
        Iterate on the tree for which this node is root.

        This will create a generator to iterate on all elements.
        """
        if self.__left is not None:
            for element in self.__left:
                yield element
        yield self.__element
        if self.__right is not None:
            for element in self.__right:
                yield element

    def __len__(self) -> int:
        """
        Count the elements in the tree for which this node is root.

        :return: the count of elements in this tree.
        """
        count = 1
        if self.__left is not None:
            count += len(self.__left)
        if self.__right is not None:
            count += len(self.__right)
        return count

    def __str__(self) -> str:
        """
        Create a string representing the tree for which this node is root.

        :return: the string representing the node.
        """
        result = ""
        if self.__left is not None:
            result += str(self.__left) + ", "
        result += str(self.__element)
        if self.__right is not None:
            result += ", " + str(self.__right)
        return result

    def add(self, node: '_BNode', comparator: Callable[[T, T], int]) -> None:
        """
        Add a node in the tree for which this node is root.

        After addition, the tree may not be balanced.

        The comparator is a fuction taking two parameters (the compared node
        elements) and returning either a negative value if the left element is
        smaller than the right one, a positive value if the left node element is
        bigger than the right one or 0 if the node elements are of same weight.

        :param node: the node to insert.
        :param comparator: the comparator to use for sorting elements.
        """
        result = comparator(node.__element, self.__element)
        if result < 0:
            if self.__left is None:
                self.__left = node
                node.__parent = self
                self.__invalidate_height()
            else:
                self.__left.add(node, comparator)
        else:
            if self.__right is None:
                self.__right = node
                node.__parent = self
                self.__invalidate_height()
            else:
                self.__right.add(node, comparator)

    def balance(self) -> '_BNode':
        """
        Balance the tree starting at this node.

        This will balance up to the root of the tree. This method should be
        called after each tree insertion for an AVL tree. Balancing the tree may
        require to change the tree root.

        :return: the new tree root.
        """
        leftHeight = _BNode.__get_height(self.__left)
        rightHeight = _BNode.__get_height(self.__right)
        if leftHeight - rightHeight > 1:
            assert isinstance(self.__left, _BNode)
            if _BNode.__get_height(self.__left.__left) >= \
                    _BNode.__get_height(self.__left.__right):
                self.__right_rotate()
            else:
                self.__left.__left_rotate()
                self.__right_rotate()
        elif rightHeight - leftHeight > 1:
            assert isinstance(self.__right, _BNode)
            if _BNode.__get_height(self.__right.__right) >= \
                    _BNode.__get_height(self.__right.__left):
                self.__left_rotate()
            else:
                self.__right.__right_rotate()
                self.__left_rotate()
        if self.__parent is not None:
            return self.__parent.balance()
        else:
            return self

    def __left_rotate(self) -> None:
        """
        Rotate this node to the left of its right child.

        The right child must exist, but not the parent.
        """
        assert isinstance(self.__right, _BNode)
        rotated = self.__right
        rotated.__parent = self.__parent
        if rotated.__parent is not None:
            if rotated.__parent.__left is self:
                rotated.__parent.__left = rotated
            elif rotated.__parent.__right is self:
                rotated.__parent.__right = rotated
        self.__right = rotated.__left
        if self.__right is not None:
            self.__right.__parent = self
        rotated.__left = self
        self.__parent = rotated
        self.__invalidate_height()

    def __right_rotate(self) -> None:
        """
        Rotate this node to the right of its left child.

        The left child must exist, but not the parent.
        """
        assert isinstance(self.__left, _BNode)
        rotated = self.__left
        rotated.__parent = self.__parent
        if rotated.__parent is not None:
            if rotated.__parent.__left is self:
                rotated.__parent.__left = rotated
            elif rotated.__parent.__right is self:
                rotated.__parent.__right = rotated
        self.__left = rotated.__right
        if self.__left is not None:
            self.__left.__parent = self
        rotated.__right = self
        self.__parent = rotated
        self.__invalidate_height()

    def search(self, comparator: Callable[[T], int]) -> Optional['_BNode']:
        """
        Find a node matching the given comparator.

        The comparator is a fuction taking one parameter (the node element) and
        returning either a negative value (if the node element is too small), a
        positive value (if the node element is too big) or 0 if the node element
        is matching.

        :param comparator: the comparator used for searching.
        :return: the found node or None if none found.
        """
        result = comparator(self.__element)
        if result == 0:
            return self
        elif result < 0 and self.__right is not None:
            return self.__right.search(comparator)
        elif result > 0 and self.__left is not None:
            return self.__left.search(comparator)
        else:
            return None

    def __invalidate_height(self) -> None:
        """
        Invalidate the height of this node.

        The previously calculated height may be obsolete, it will have to be
        recalculated if needed.
        """
        self.__height = -1
        if self.__parent is not None:
            self.__parent.__invalidate_height()

    @property
    def element(self) -> T:
        """
        Get the element inside this node.

        :return: the element inside this node.
        """
        return self.__element

    @property
    def height(self) -> int:
        """
        Get the heigh of the tree for which this node is root.

        If the height is unknown, it will be calculated.
        """
        if self.__height < 0:
            leftHeight = _BNode.__get_height(self.__left)
            rightHeight = _BNode.__get_height(self.__right)
            self.__height = max(leftHeight, rightHeight) + 1
        return self.__height

    @staticmethod
    def __get_height(node: Optional['_BNode']) -> int:
        """
        Get the heigh of the tree for which given node is root.

        :param node: the node for which to get the height.
        """
        return -1 if node is None else node.height


class AvlTree(Generic[T]):
    """
    An AVL binary tree.

    The tree is always balanced. It contains arbitrary elements. Methods must be
    provided to the tree in order to sort elements and can also be provided to
    search elements.

    An AvlTree is iterable. Elements will then be given in ascending order.

    Note that element removal is not implemented.

    :Example:

    >>> tree = AvlTree(lambda a, b: a["value"] - b["value"])
    >>> len(tree)
    0
    >>> tree.height
    -1
    >>> print(tree)
    <empty>

    >>> tree.add({"value": 5})
    >>> tree.add({"value": 12})
    >>> tree.add({"value": 1})
    >>> tree.add({"value": 9})
    >>> tree.add({"value": 48})
    >>> tree.add({"value": 27})
    >>> tree.add({"value": 6})

    >>> len(tree)
    7
    >>> tree.height
    3
    >>> print(tree)
    {'value': 1}, {'value': 5}, {'value': 6}, {'value': 9}, {'value': 12}, \
{'value': 27}, {'value': 48}
    >>> tree.search({"value": 12})
    {'value': 12}
    >>> tree.search(lambda e: e["value"] - 27)
    {'value': 27}
    >>> tree.search({"value": 128})
    """

    def __init__(self, comparator: Callable[[T, T], int], element: Optional[T] = None) -> None:
        """
        Create the tree.

        The tree can contain a first element, or be empty if no element
        provided.

        The comparator is a fuction taking two parameters (the compared
        elements) and returning either a negative value if the left element is
        smaller than the right one, a positive value if the left node element is
        bigger than the right one or 0 if the node elements are of same weight.

        :param comparator: the comparator used to sort elements.
        :param element: the element to insert in the tree (optional).
        """
        self.__comparator: Callable[[T, T], int] = comparator
        self.__root: Optional[_BNode] = \
            None if element is None else _BNode(element)

    def __del__(self) -> None:
        """
        Delete the tree.

        This deletion should imply node deletion too, but because there are
        mutual dependencies, they may not be correctly garbage collected, so we
        need to explicitely delete them.
        """
        if self.__root is not None:
            self.__root.saw_children()

    def __iter__(self) -> Iterator[T]:
        """
        Iterate on the tree.

        This will create a generator to iterate on all elements.
        """
        if self.__root is not None:
            for element in self.__root:
                yield element

    def __len__(self) -> int:
        """
        Return the count of elements in this tree.

        :return: the count of elements in the tree.
        """
        return 0 if self.__root is None else len(self.__root)

    def __str__(self) -> str:
        """
        Create a string representing the tree.

        :return: the string representing the tree.
        """
        if self.__root is None:
            return "<empty>"
        else:
            return str(self.__root)

    def add(self, element: T) -> None:
        """
        Add an element to the tree.

        The tree will be automatically balanced after addition.

        :param element: the element to add to the tree.
        """
        node = _BNode(element)
        if self.__root is None:
            self.__root = node
        else:
            self.__root.add(node, self.__comparator)
            self.__root = node.balance()

    def search(self, data: Union[T, Callable[[T], int]]) -> Optional[T]:
        """
        Search an element in the tree.

        The search can either be done by comparing a given element to the ones
        in the tree, or by providing a comparator function. The comparator is a
        function taking one parameter (the node element) and returning either a
        negative value (if the node element is too small), a positive value (if
        the node element is too big) or 0 if the node element is matching.

        :param data: either an element to search in the tree or a comparison
        function.
        """
        if self.__root is None:
            result = None
        elif callable(data):
            result = self.__root.search(data)
        else:
            result = self.__root.search(
                lambda e: self.__comparator(e, data))  # type: ignore
        return None if result is None else result.element

    @property
    def height(self) -> int:
        """
        :return: the height of the tree, or -1 if empty.
        """
        return -1 if self.__root is None else self.__root.height
