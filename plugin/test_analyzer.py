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

import os
import unittest

from typing import Dict, List

from gi.repository import GLib

from .analyzer import GrammalecteRequester, GrammalecteAnalyzer
from .config import GrammalecteConfig
from .error import GrammalecteError


TEXT = ["Quoi ? Racontes ! Racontes-moi ! Bon sangg, parles !",
        "Oui. Il y a des menteur partout. Je suit sidéré par la",
        "brutales arrogance de cette homme-là. Quelle salopard ! Un",
        "escrocs de la pire espece. Quant sera t’il châtiés pour ses",
        "mensonge ?             Merde ! J’en aie marre."]
RESULT: Dict[str, int] = {'WORD': 2,
                          'conf': 1,
                          'conj': 2,
                          'esp': 1,
                          'gn': 6,
                          'imp': 2,
                          'nbsp': 2,
                          'ppas': 1,
                          'tu': 1,
                          'vmode': 1}


class MockRequester(GrammalecteRequester):
    """ Mock for the requester """

    def __init__(self, name: str, analyzer: GrammalecteAnalyzer, concat: str, ending_callback):
        self.name = name
        self.config = GrammalecteConfig()
        self.config.set_value(GrammalecteConfig.CONCAT_LINES, concat != " ")
        self.example = concat.join(TEXT)
        if concat == " ":
            self.example = self.example + "\n" + self.example
        else:
            self.example = self.example + concat + concat + self.example
        self.ending_callback = ending_callback
        self.found_errors: Dict[str, int] = {}
        analyzer.connect("analyze-finished", self.on_result)

    def get_text(self):
        """ Get the text of the requester """
        return self.example

    def get_config(self):
        """ Get the configuration for the requester """
        return self.config

    def on_result(self, analyzer: GrammalecteAnalyzer, requester: GrammalecteRequester, result: List[GrammalecteError]) -> None:
        """ Set the result of the request """
        if requester is not self:
            return
        for err_in_paragraph in result:
            allLines: List[str] = self.example.splitlines()
            option = err_in_paragraph.option
            lineStart, charStart = err_in_paragraph.start
            lineEnd, charEnd = err_in_paragraph.end
            if lineStart < (len(allLines) / 2):
                faulty = allLines[lineStart]
                before = faulty[max(0, charStart - 10):charStart] + " [ "
                if charStart > 10:
                    before = "…" + before
                if lineEnd != lineStart:
                    charEnd = len(faulty)
                after = " ] " + faulty[charEnd:min(len(faulty), charEnd + 10)]
                if charEnd < len(faulty) - 10:
                    after = after + "…"
                if lineEnd != lineStart:
                    after = after + "…(!)"
                displayed = self.name + " - l" + \
                    str(lineStart + 1) + ": " + before + \
                    faulty[charStart:charEnd] + after
                if not err_in_paragraph.description:
                    description = "(pas de description)"
                else:
                    description = err_in_paragraph.description
                    if err_in_paragraph.url:
                        description += " (" + err_in_paragraph.url + ")"
                displayed += "\n  > " + description + "\n  Suggestions: " + \
                    str(err_in_paragraph.suggestions)
                print(displayed)
            self.found_errors[option] = self.found_errors.get(option, 0) + 1
        self.ending_callback()


class TestGrammalecteAnalyzer(unittest.TestCase):
    def setUp(self):
        GrammalecteConfig().set_value(GrammalecteConfig.ANALYZE_PARALLEL_COUNT, 2, 1)
        self.mainloop = GLib.MainLoop()
        self.analyzer = GrammalecteAnalyzer()
        self.requesters = [MockRequester(
            "Standard", self.analyzer, "\n", lambda: self._terminate_process()),
            MockRequester(
            "Windows", self.analyzer, "\r\n", lambda: self._terminate_process()),
            MockRequester(
            "Single", self.analyzer, " ", lambda: self._terminate_process())]
        self.process_count = 3

    def test_analyze(self):
        for requester in self.requesters:
            self.analyzer.add_request(requester)
        self.mainloop.run()
        for requester in self.requesters:
            for key in RESULT:
                self.assertEqual(requester.found_errors.get(key, -1), RESULT[key] * 2,
                                 "Bad count for " + key + " in " + requester.name)
            for key in requester.found_errors:
                self.assertIn(key, RESULT, "Bad error type " +
                              key + " in " + requester.name)

    def _terminate_process(self):
        self.process_count -= 1
        if self.process_count <= 0:
            self.mainloop.quit()


if __name__ == '__main__':
    unittest.main()
