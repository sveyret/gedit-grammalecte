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

from typing import Any, Dict, Iterable, Iterator, List, Tuple

from .config import GrammalecteConfig, _


class _GrammalecteResultEntry:
    """
    Entries of the Grammalecte result dictionnary.
    """
    LINE_START = "nStartY"
    CHAR_START = "nStartX"
    LINE_END = "nEndY"
    CHAR_END = "nEndX"
    OPTION = "sType"
    RULE = "sRuleId"
    DESCRIPTION = "sMessage"
    URL = "URL"
    SUGGESTIONS = "aSuggestions"
    CTX_SPELL = "sValue"
    CTX_GRAMMAR = "sUnderlined"
    CTX_BEFORE = "sBefore"
    CTX_AFTER = "sAfter"


class _ErrorContext():
    """
    The error context, i.e. the problematic word, the words before and the words
    after.
    """

    def __init__(self, analyzerFormat: Dict[str, Any]) -> None:
        """
        Create an error context.

        :param analyzerFormat: The analyzer result.
        """
        self.erroneous: str
        if _GrammalecteResultEntry.CTX_GRAMMAR in analyzerFormat:
            self.erroneous = analyzerFormat[_GrammalecteResultEntry.CTX_GRAMMAR]
        elif _GrammalecteResultEntry.CTX_SPELL in analyzerFormat:
            self.erroneous = analyzerFormat[_GrammalecteResultEntry.CTX_SPELL]
        else:
            self.erroneous = ""
        self.before: str = analyzerFormat.get(
            _GrammalecteResultEntry.CTX_BEFORE, "")
        self.after: str = analyzerFormat.get(
            _GrammalecteResultEntry.CTX_AFTER, "")

    def __iter__(self):
        """
        Iterate on erroneous item, before and after.
        """
        yield self.erroneous
        yield self.before
        yield self.after


class GrammalecteError():
    """
    An error found in the document.
    """
    SPELL_OPTION = "WORD"

    def __init__(self, analyzerFormat: Dict[str, Any]) -> None:
        """
        Create the error from an analyzer result.

        :param analyzerFormat: The analyzer result.
        """
        self.start: Tuple[int, int] = (
            analyzerFormat[_GrammalecteResultEntry.LINE_START] - 1,
            analyzerFormat[_GrammalecteResultEntry.CHAR_START]
        )
        self.end: Tuple[int, int] = (
            analyzerFormat[_GrammalecteResultEntry.LINE_END] - 1,
            analyzerFormat[_GrammalecteResultEntry.CHAR_END]
        )
        self.option: str = analyzerFormat[_GrammalecteResultEntry.OPTION]
        self.rule: str = analyzerFormat.get(_GrammalecteResultEntry.RULE, "")
        self.description: str = analyzerFormat.get(_GrammalecteResultEntry.DESCRIPTION, _(
            "Unknown word.") if self.option == GrammalecteError.SPELL_OPTION else "")
        self.url: str = analyzerFormat.get(_GrammalecteResultEntry.URL, "")
        self.suggestions: List[str] = analyzerFormat[_GrammalecteResultEntry.SUGGESTIONS]
        self.context: _ErrorContext = _ErrorContext(analyzerFormat)

    def __str__(self) -> str:
        return "Analysis error [" + str(self.start[0]) + "," + \
            str(self.start[1]) + ":" + str(self.end[0]) + \
            "," + str(self.end[1]) + "]: " + self.option

    @staticmethod
    def buildErrorList(analyzerFormat: List[Dict[str, Any]]) -> List['GrammalecteError']:
        return [GrammalecteError(e) for e in analyzerFormat]

    @staticmethod
    def filterIgnored(errors: Iterable['GrammalecteError'], config: GrammalecteConfig) -> Iterator['GrammalecteError']:
        ignoredErrors = []
        usedIgnored = []
        for ignored in config.get_all_values(GrammalecteConfig.IGNORED_ERRORS):
            ignoredErrors.append(tuple(ignored))
        for error in errors:
            context = tuple(error.context)
            if context in ignoredErrors:
                if context not in usedIgnored:
                    usedIgnored.append(context)
            else:
                yield error
        for ignored in ignoredErrors:
            if not ignored in usedIgnored:
                config.del_value(
                    GrammalecteConfig.IGNORED_ERRORS, list(ignored))
