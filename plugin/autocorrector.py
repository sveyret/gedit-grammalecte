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

from typing import Callable, List, Optional, Tuple

import sys

from gi.repository import Gdk, Gtk, GLib, GObject, Pango

from .analyzer import GrammalecteRequester, GrammalecteAnalyzer
from .config import GrammalecteConfig
from .error import GrammalecteError
from .errorstore import GrammalecteErrorStore
from .popupmenu import CorrectionProcess, GrammalectePopupMenu


class _BufferData:
    """
    The data for the current buffer.
    """
    __ERROR_TAG = "grammalecte_error"

    def __init__(self, text_buffer: Optional[Gtk.TextBuffer], on_changed: Callable[[], None]) -> None:
        """
        Initialize the buffer data.

        :param text_buffer: The real text buffer.
        :param changed_event: The function called on changed event.
        """
        self.text_buffer: Optional[Gtk.TextBuffer] = text_buffer
        self.error_tag: Gtk.TextTag
        if self.text_buffer is not None:
            self.error_tag = self.text_buffer.get_tag_table().lookup(_BufferData.__ERROR_TAG)
            if self.error_tag is None:
                self.error_tag = self.text_buffer.create_tag(
                    _BufferData.__ERROR_TAG, underline=Pango.Underline.ERROR)
            self.__eventChangedId = self.text_buffer.connect(
                "changed", on_changed)

    def set_errors(self, store: GrammalecteErrorStore, buffer: Gtk.TextBuffer) -> bool:
        """
        Set the result of the request.

        :param requester: The requester of the analyze.
        :param result: The result of the analyze.
        """
        if buffer is not self.text_buffer:
            return False
        self.clear_tag()
        for error in store:
            start = self.__convert_limits(error.start)
            end = self.__convert_limits(error.end)
            buffer.apply_tag(self.error_tag, start, end)
        self.__cur_buffer = None
        return False

    def terminate(self) -> None:
        """
        Terminate usage of this buffer data.
        """
        if self.text_buffer is not None:
            self.text_buffer.disconnect(self.__eventChangedId)
            self.clear_tag()
            self.text_buffer = None

    def clear_tag(self) -> None:
        """
        Clear the tag from the buffer text.
        """
        if self.text_buffer is not None:
            self.text_buffer.remove_tag(
                self.error_tag, self.text_buffer.get_start_iter(), self.text_buffer.get_end_iter())

    def __convert_limits(self, position: Tuple[int, int]) -> Gtk.TextIter:
        """
        Convert the limits from error position to TextIter.

        :param position: The position to convert.
        :return: The position as TextIter.
        """
        assert self.text_buffer is not None
        maxLine = self.text_buffer.get_end_iter().get_line()
        line, offset = position
        if line > maxLine:
            line = maxLine
        text_iter = self.text_buffer.get_iter_at_line(line)
        if offset > text_iter.get_chars_in_line():
            offset = text_iter.get_chars_in_line()
        text_iter.set_line_offset(offset)
        return text_iter


class GrammalecteAutoCorrector(GrammalecteRequester, CorrectionProcess):
    """
    The automatic corrector.
    """
    __TICK_DURATION = 100
    __TICK_OFF = -sys.maxsize - 1
    __TOOLTIP = "{2}<span foreground=\"red\" style=\"italic\">{1}</span>{3}\n" \
        + "<span foreground=\"blue\" weight=\"bold\">{0}</span>"

    def __init__(self, view: Gtk.TextView, config: GrammalecteConfig, analyzer: GrammalecteAnalyzer) -> None:
        """
        Initialize the corrector.

        :param view: The view to connect to analyzer.
        :param config: The configuration associated to the view.
        :param analyzer: The error analyzer.
        """
        self.__config: GrammalecteConfig = config
        self.__analyzer: GrammalecteAnalyzer = analyzer
        self.__requested: bool = False
        self.__cur_buffer: Optional[Gtk.TextBuffer] = None
        self.__store: GrammalecteErrorStore = GrammalecteErrorStore()
        self.__menu_position: Gtk.TextIter = view.get_buffer().get_start_iter()
        self.__tick_count: int = 1

        self.__buffer_data: _BufferData = _BufferData(
            view.get_buffer(), self.on_content_changed)

        self.__eventAnalStartId = self.__analyzer.connect(
            "analyze-started", self.on_analyze_started)
        self.__eventAnalFinishId = self.__analyzer.connect(
            "analyze-finished", self.on_analyze_finished)
        self.__eventTooltipId = view.connect(
            "query-tooltip", self.on_query_tooltip)
        self.__eventMouseClicked = view.connect(
            "button-press-event", self.on_mouse_clicked)
        self.__eventPopupMenu = view.connect(
            "popup-menu", self.on_popup_menu)
        self.__eventPopulatePopup = view.connect(
            "populate-popup", self.on_populate_popup)
        self.__eventBufferId = view.connect(
            "notify::buffer", self.on_buffer_changed)
        self.__eventConfigUpdated = self.__config.connect(
            "updated", self.on_conf_updated)
        self.__eventConfigCleared = self.__config.connect(
            "cleared", self.on_conf_cleared)

        view.set_property("has_tooltip", True)
        self.__ask_request()
        GObject.timeout_add(
            GrammalecteAutoCorrector.__TICK_DURATION, self.__add_request)

    def disconnect(self, view: Gtk.TextView) -> None:
        """
        Disconnect the corrector from the view.

        :param view: The view to disconnect from auto-analyzer.
        """
        self.__tick_count = GrammalecteAutoCorrector.__TICK_OFF
        self.__config.disconnect(self.__eventConfigCleared)
        self.__config.disconnect(self.__eventConfigUpdated)
        view.disconnect(self.__eventBufferId)
        view.disconnect(self.__eventPopulatePopup)
        view.disconnect(self.__eventPopupMenu)
        view.disconnect(self.__eventMouseClicked)
        view.disconnect(self.__eventTooltipId)
        self.__analyzer.disconnect(self.__eventAnalFinishId)
        self.__analyzer.disconnect(self.__eventAnalStartId)

        self.__buffer_data.terminate()
        self.__cur_buffer = None

    def on_content_changed(self, *_):
        """
        Called when buffer content changed.
        """
        self.__ask_request()

    def on_analyze_started(self, _, requester: GrammalecteRequester) -> None:
        """
        Indicate that analyze has started, so other requests can be made.

        :param requester: The requester of the analyze.
        """
        if requester is self:
            self.__requested = False

    def on_analyze_finished(self, _, requester: GrammalecteRequester, result: Optional[List[GrammalecteError]]) -> None:
        """
        Set the result of the request.

        :param requester: The requester of the analyze.
        :param result: The result of the analyze.
        """
        if requester is not self:
            return
        assert self.__cur_buffer is not None
        self.__store = GrammalecteErrorStore()
        if result is not None:
            self.__store.add_all(
                GrammalecteError.filterIgnored(result, self.__config))
        GLib.idle_add(
            self.__buffer_data.set_errors, self.__store, self.__cur_buffer)
        self.__cur_buffer = None

    def on_query_tooltip(self, view: Gtk.TextView, x: int, y: int, keyboard: bool, tooltip: Gtk.Tooltip) -> bool:
        """
        Manage tooltip query event.

        :param view: The text view.
        :param x: The x position.
        :param y: The y position.
        :param keyboard: True if event comes from keyboard.
        :param tooltip: The queried tooltip.
        :return: True to prevent other handlers from being called.
        """
        position: Gtk.TextIter
        if keyboard:
            buff = view.get_buffer()
            position = buff.get_iter_at_mark(buff.get_insert())
        else:
            buffPos = view.window_to_buffer_coords(
                Gtk.TextWindowType.TEXT, x, y)
            _, position = view.get_iter_at_location(*buffPos)
        line = position.get_line()
        offset = position.get_line_offset()
        error = self.__store.search((line, offset))
        if error is not None:
            tooltip.set_markup(GrammalecteAutoCorrector.__TOOLTIP.format(
                error.description, *tuple(error.context)))
            return True
        else:
            return False

    def on_mouse_clicked(self, view: Gtk.TextView, event: Gdk.EventButton) -> bool:
        """
        Manage the mouse clicked event.

        :param view: The text view.
        :param event: The button event.
        :return: True to prevent other handlers from being called.
        """
        if event.button == 3:
            coords = view.window_to_buffer_coords(
                Gtk.TextWindowType.TEXT, int(event.x), int(event.y))
            _, self.__menu_position = view.get_iter_at_location(*coords)
        return False

    def on_popup_menu(self, view: Gtk.TextView) -> bool:
        """
        Manage the popup menu event.

        :param view: The text view.
        :return: True to prevent other handlers from being called.
        """
        buff = view.get_buffer()
        self.__menu_position = buff.get_iter_at_mark(buff.get_insert())
        return False

    def on_populate_popup(self, view: Gtk.TextView, menu: Gtk.Menu) -> None:
        """
        Manage the populate popup event.

        :param view: The text view.
        :param menu: The menu to populate.
        """
        line = self.__menu_position.get_line()
        offset = self.__menu_position.get_line_offset()
        error = self.__store.search((line, offset))
        if error is not None:
            GrammalectePopupMenu(menu, error, self)

    def on_buffer_changed(self, view: Gtk.TextView, *_) -> None:
        """
        Called when the buffer was changed.

        :param view: The text view.
        """
        self.__buffer_data.terminate()
        self.__buffer_data = _BufferData(
            view.get_buffer(), self.on_content_changed)
        self.__ask_request()

    def on_conf_updated(self, config: GrammalecteConfig, level: int, xPath: str, *_) -> None:
        """
        Manage the configuration updated event.

        :param config: The configuration.
        :param level: The updated level.
        :param xPath: The modified configuration item.
        """
        if xPath in (
                GrammalecteConfig.LOCALE_DIR,
                GrammalecteConfig.ANALYZE_PARALLEL_COUNT,
                GrammalecteConfig.ANALYZE_WAIT_TICKS):
            return
        self.__ask_request()

    def on_conf_cleared(self, *_) -> None:
        """
        Manage the configuration cleared event.
        """
        self.__ask_request()

    def __ask_request(self) -> None:
        """
        A new request is needed. Wait for some idle time before starting it.
        """
        if not self.__requested:
            self.__tick_count = self.get_config().get_value(
                GrammalecteConfig.ANALYZE_WAIT_TICKS)

    def __add_request(self) -> bool:
        """
        Check if idle time is enough, before executing the request.

        :return: True to continue execution, False to stop timer.
        """
        if self.__tick_count == GrammalecteAutoCorrector.__TICK_OFF:
            return False  # Stop auto-execution

        if self.__tick_count >= 0:
            self.__tick_count -= 1
        if self.__tick_count == 0:
            self.__requested = True
            self.__analyzer.add_request(self)
        return True

    def get_config(self) -> GrammalecteConfig:
        """
        :return: The configuration.
        """
        return self.__config

    def get_buffer(self) -> Gtk.TextBuffer:
        """
        :return: The text buffer.
        """
        return self.__buffer_data.text_buffer

    def get_text(self) -> str:
        """
        Get the text for the requester. This will save the buffer currently
        being analyzed.

        :return: The text.
        """
        if self.__buffer_data is None:
            return ""
        self.__cur_buffer = self.__buffer_data.text_buffer
        assert self.__cur_buffer is not None
        return self.__cur_buffer.get_slice(
            self.__cur_buffer.get_start_iter(), self.__cur_buffer.get_end_iter(), True)
