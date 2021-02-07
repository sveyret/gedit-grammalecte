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

from typing import Dict, Optional

from gi.repository import Gedit, Gio, GLib, GObject, Gtk

from .application import GrammalecteApplication, get_application
from .config import GrammalecteConfig, _
from .config_dlg import GrammalecteConfigDlg
from .view import GrammalecteView, get_view

_windows: Dict[Gtk.Window, 'GrammalecteWindow'] = {}


class GrammalecteWindow(GObject.Object, Gedit.WindowActivatable):
    """
    The window activated part.
    """
    __gtype_name__ = "GrammalecteWindow"

    __STATUS_BAR_TAG = "Grammalecte"

    window: Gtk.Window = GObject.property(type=Gedit.Window)

    def __init__(self) -> None:
        """
        Initialize the object.
        """
        GObject.Object.__init__(self)
        self.window: Gtk.Window
        self.__actionGroup: Gtk.ActionGroup
        self.__sbContext: int
        self.__eventAnalyzeStartId: Optional[int] = None
        self.__eventAnalyzeFinishId: Optional[int] = None

    def do_activate(self) -> None:
        """
        Called when window part of the plugin should be activated.
        """
        self.__sbContext = self.window.get_statusbar().get_context_id(
            GrammalecteWindow.__STATUS_BAR_TAG)
        self.__connect_analyzer(True)
        self.window.connect("notify::application", self.on_application_change)
        action: Gtk.Action
        action = Gio.SimpleAction.new("ConfigGrammalecte", None)
        action.connect("activate", self.on_menu_config)
        self.window.add_action(action)
        action = Gio.SimpleAction.new_stateful(
            "AutoGrammalecte", None, GLib.Variant.new_boolean(False))
        action.connect("change-state", self.on_menu_auto)
        self.window.add_action(action)
        _windows[self.window] = self

    def on_application_change(self, *ignored) -> None:
        self.__connect_analyzer(False)
        self.__connect_analyzer(True)

    def do_deactivate(self) -> None:
        """
        Called when window part of the plugin should be deactivated.
        """
        if _windows.get(self.window) == self:
            del _windows[self.window]
        self.window.remove_action("AutoGrammalecte")
        self.window.remove_action("ConfigGrammalecte")
        self.__connect_analyzer(False)

    def on_analyze_started(self, *ignored) -> None:
        """
        Grammalecte analyze started.
        """
        self.window.get_statusbar().push(
            self.__sbContext, _("Linguistic checking in progress..."))

    def on_analyze_finished(self, *ignored) -> None:
        """
        Grammalecte analyze terminated.
        """
        self.window.get_statusbar().pop(self.__sbContext)

    def do_update_state(self) -> None:
        """
        Update the state.
        """
        view = self.__get_active_view()
        sensible = view is not None and not view.is_readonly()
        action = self.window.lookup_action("AutoGrammalecte")
        action.set_enabled(sensible)
        action.set_state(GLib.Variant.new_boolean(
            view is not None and view.is_auto_check_on()))
        action = self.window.lookup_action("ConfigGrammalecte")
        action.set_enabled(sensible)

    def on_menu_auto(self, action: Gio.Action, state: GLib.Variant) -> None:
        """
        Manage automatic toggle menu.

        :param action: The action calling the function.
        :param state: The new state.
        """
        action.set_state(state)
        view = self.__get_active_view()
        if view is not None and not view.is_readonly():
            view.set_auto_analyze(state.get_boolean())

    def on_menu_config(self, *ignored):
        """
        Change configuration.
        """
        GrammalecteConfigDlg().run_dialog(
            self.window, self.__get_active_view().get_config())

    def __connect_analyzer(self, connect: bool) -> None:
        """
        Connect to the analyzer, or diconnect from it.

        :param connect: True to create connection, false to remove it.
        """
        app = get_application(self.window.get_application())
        if app:
            if connect:
                self.__eventAnalyzeStartId = app.get_analyzer().connect(
                    "analyze-started", self.on_analyze_started)
                self.__eventAnalyzeFinishId = app.get_analyzer().connect(
                    "analyze-finished", self.on_analyze_finished)
            else:
                if self.__eventAnalyzeFinishId is not None:
                    app.get_analyzer().disconnect(self.__eventAnalyzeFinishId)
                self.__eventAnalyzeFinishId = None
                if self.__eventAnalyzeStartId is not None:
                    app.get_analyzer().disconnect(self.__eventAnalyzeStartId)
                self.__eventAnalyzeStartId = None

    def __get_active_view(self) -> Optional[GrammalecteView]:
        """
        Get the active Grammalecte view.
        """
        view = self.window.get_active_view()
        return None if view is None else get_view(view)


def get_window(window: Gtk.Window) -> Optional[GrammalecteWindow]:
    """
    :return: The grammalecte window associated to the given window, may be none.
    """
    return _windows.get(window)
