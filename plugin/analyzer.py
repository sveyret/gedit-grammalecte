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

from typing import Dict, Iterator, List, Optional, Tuple

from grammalecte import GrammarChecker, text as Text
from queue import Queue
from threading import Thread

from gi.repository import GLib, GObject

from .config import GrammalecteConfig, _
from .error import GrammalecteError


class _IgnoredException(Exception):
    """
    An exception which should be ignored by the rest of execution.
    """
    pass


class GrammalecteRequester:
    """
    An object which can request an analyzis.

    Any object calling the analyzer must override all these methods.
    """

    def get_config(self) -> GrammalecteConfig:
        """
        Get the configuration for the requester.

        :return: the requester configuration.
        """
        pass

    def get_text(self) -> str:
        """
        Get the text of the requester.

        :return: the text to be analyzed.
        """
        pass


class _SingleAnalyzer(Thread):
    """
    Class managing a single grammar analyzis.

    There should not be many instances of the single analyzer to prevent from
    saturating the CPU. The user should be able to choose the count of analyzer
    working at a given time. The single analyzer is actually a thread to be able
    to run in non blocking state.
    """

    def __init__(self, analyzer: 'GrammalecteAnalyzer', requester: GrammalecteRequester) -> None:
        """
        Initialize the analyzer.

        :param analyzer: The analyzer creating the thread.
        :param requester: The requester of the analyze.
        """
        Thread.__init__(self)
        self._analyzer: 'GrammalecteAnalyzer' = analyzer
        self._requester: GrammalecteRequester = requester

    def run(self) -> None:
        """
        Run the thread. Always call the analyzer when finished, even if error
        occured.
        """
        found_errors: Optional[List[GrammalecteError]] = None
        try:
            found_errors = self.__call_grammalecte()
        except _IgnoredException:
            pass
        finally:
            self._analyzer._terminate_request(self._requester, found_errors)

    def __call_grammalecte(self) -> List[GrammalecteError]:
        """
        Prepare and call Grammalecte.

        :return: The list (may be empty) of errors.
        """
        config = self._requester.get_config()
        if config is None:
            raise _IgnoredException

        # Set parameters to Grammalecte
        grammarChecker = GrammarChecker("fr")
        grammarChecker.getGCEngine().setOptions(
            config.get_value(GrammalecteConfig.ANALYZE_OPTIONS))
        for ignoredRule in config.get_all_values(GrammalecteConfig.IGNORED_RULES):
            grammarChecker.gce.ignoreRule(ignoredRule)

        # Analyze text
        found_errors: List[GrammalecteError] = []
        for text, lineDefinition in _SingleAnalyzer.__createParagraphs(
                self._requester.get_text(), config.get_value(GrammalecteConfig.CONCAT_LINES)):
            grammErrs, spellErrs = grammarChecker.getParagraphErrors(
                text, bContext=True, bSpellSugg=True)
            grammErrs, spellErrs = Text.convertToXY(
                grammErrs, spellErrs, lineDefinition)
            found_errors.extend(GrammalecteError.buildErrorList(grammErrs))
            found_errors.extend(GrammalecteError.buildErrorList(spellErrs))
        return found_errors

    @staticmethod
    def __createParagraphs(text: str, concatLines: bool) -> Iterator[Tuple[str, List[Tuple[int, int, int]]]]:
        """
        Create paragraphs from the input text. Paragraphs may be composed of
        multiple lines.

        :param text: The text to split into paragraphs.
        :param concatLines: True to concat lines (until an empty one) to create
        paragraphs.
        :return: A generator of paragraph data (i.e. the text and original line
        definition).
        """
        lines: List[Tuple[int, str]] = []
        for lineIndex, line in enumerate(text.splitlines(), 1):
            createParagraph: bool = False
            if not concatLines:
                lines.append((lineIndex, line))
                createParagraph = True
            elif line.strip():
                lines.append((lineIndex, line))
            elif lines:
                createParagraph = True
            if createParagraph:
                parText, lineDefinition = Text.createParagraphWithLines(lines)
                yield parText, lineDefinition
                lines = []
        if lines:
            parText, lineDefinition = Text.createParagraphWithLines(lines)
            yield parText, lineDefinition


class GrammalecteAnalyzer(GObject.GObject):
    """
    Class managing grammar analyzis.

    There should not be many instances of the analyzer. A good choice is to
    create one single instance for the application. The analyzer starts as much
    single analyzer threads as there are requests, up to the configured limit.
    The analyzer sends events each time a new thread is started or finished.
    """
    __gtype_name__ = "GrammalecteAnalyzer"
    __gsignals__ = {
        "analyze-started": (GObject.SignalFlags.RUN_LAST, None, (object,)),
        "analyze-finished": (GObject.SignalFlags.RUN_LAST, None, (object, object))
    }

    def __init__(self) -> None:
        """
        Initialize the thread.
        """
        GObject.GObject.__init__(self)
        self._queue: 'Queue[GrammalecteRequester]' = Queue()
        self._free_room: int = GrammalecteConfig().get_value(
            GrammalecteConfig.ANALYZE_PARALLEL_COUNT)

    def add_request(self, requester: GrammalecteRequester) -> None:
        """
        Add a new request to the analyzer. The request may not be analyzed
        immediately but is added to the request queue.

        :param requester: The requester to add to the queue.
        """
        self._queue.put(requester)
        self.__start_request()

    def _terminate_request(self, requester: GrammalecteRequester, found_errors: Optional[List[GrammalecteError]]) -> None:
        """
        This method is to be called by the analyzer thread to warn that its
        analyze is finished.

        :param requester: The requester used for this analyze.
        :param found_errors: The errors found by analyze, or None if analyze did
        not finish correctly.
        """
        self._free_room += 1
        self.emit("analyze-finished", requester, found_errors)
        self.__start_request()

    def __start_request(self) -> None:
        """
        Check if a new thread can be executed (i.e. thread limit is not reached
        yet and there is at least one request in the queue) and execute it if
        possible.
        """
        if self._free_room > 0 and not self._queue.empty():
            self._free_room -= 1
            requester = self._queue.get()
            thread = _SingleAnalyzer(self, requester)
            self.emit("analyze-started", requester)
            thread.start()
