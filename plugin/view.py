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

from gi.repository import Gio, Gedit, GObject, Gtk

from .application import get_application
from .autocorrector import GrammalecteAutoCorrector
from .config import GrammalecteConfig, SelfConfigContainer

_views: Dict[Gtk.TextView, 'GrammalecteView'] = {}


class GrammalecteView(GObject.Object, Gedit.ViewActivatable, SelfConfigContainer):
    """
    The view activated part.
    """
    __gtype_name__ = "GrammalecteView"

    __CONFIG_METADATA = "metadata::gedit-grammalecte"

    view: Gtk.TextView = GObject.property(type=Gedit.View)

    def __init__(self) -> None:
        """
        Initialize the object.
        """
        GObject.Object.__init__(self)
        self.__config: GrammalecteConfig
        self.__autocorrector: Optional[GrammalecteAutoCorrector]
        self.view: Gtk.TextView

    def do_activate(self) -> None:
        """
        Called when view part of the plugin should be activated.
        """
        self.__config = GrammalecteConfig(self)
        self.__autocorrector = None
        self.__eventDocLoadedId = self.view.get_buffer().connect(
            "loaded", self.on_doc_loaded)
        self.__eventDocSavedId = self.view.get_buffer().connect(
            "saved", self.on_doc_saved)
        if self.is_auto_check_on():
            self.__set_auto_analyze(True)
        _views[self.view] = self

    def do_deactivate(self) -> None:
        """
        Called when view part of the plugin should be deactivated.
        """
        if _views.get(self.view) == self:
            del _views[self.view]
        self.__set_auto_analyze(False)
        self.view.get_buffer().disconnect(self.__eventDocSavedId)
        self.view.get_buffer().disconnect(self.__eventDocLoadedId)
        self.__config.save()

    def do_update_state(self) -> None:
        """
        Called when view should be updated.
        """
        pass

    def set_auto_analyze(self, active: bool) -> None:
        """
        Set auto-analyze to active or not.

        :param active: indicate if auto-analyze must be active or not.
        """
        self.__config.set_value(GrammalecteConfig.AUTO_ANALYZE_ACTIVE, active)
        self.__set_auto_analyze(active)

    def __set_auto_analyze(self, active: bool) -> None:
        """
        Set auto-analyze without changing the configuration.

        :param active: indicate if auto-analyze must be active or not.
        """
        app = get_application(self.view.get_toplevel().get_application())
        if app:
            if active and self.__autocorrector is None:
                self.__autocorrector = GrammalecteAutoCorrector(
                    self.view, self.__config, app.get_analyzer())
            elif not active and self.__autocorrector is not None:
                self.__autocorrector.disconnect(self.view)
                self.__autocorrector = None

    def on_doc_loaded(self, document: Gtk.TextBuffer) -> None:
        """
        Manage the document loaded event.

        :param document: The loaded document.
        """
        self.__config = GrammalecteConfig(self)
        if (self.__autocorrector is not None) != self.is_auto_check_on():
            self.__set_auto_analyze(self.is_auto_check_on())

    def on_doc_saved(self, document: Gtk.TextBuffer) -> None:
        """
        Manage the document saved event.

        :param document: The saved document.
        """
        self.__config.save()

    def get_self_config(self) -> str:
        """
        Get the configuration from file metadata.

        :return: The configuration string.
        """
        config = None
        current_file = self.view.get_buffer().get_file().get_location()
        if current_file is not None:
            info = current_file.query_info(
                GrammalecteView.__CONFIG_METADATA,
                Gio.FileQueryInfoFlags.NONE,
                None)
            config = info.get_attribute_as_string(
                GrammalecteView.__CONFIG_METADATA)
        if config is None:
            config = SelfConfigContainer.EMPTY
        return config

    def set_self_config(self, config: str) -> None:
        """
        Set the configuration in file metadata.

        :param config: The configuration string.
        """
        current_file = self.view.get_buffer().get_file().get_location()
        if current_file is not None:
            current_file.set_attribute_string(
                GrammalecteView.__CONFIG_METADATA,
                config,
                Gio.FileQueryInfoFlags.NONE,
                None)

    def is_auto_check_on(self) -> bool:
        """
        Indicate if automatic check is on.

        :return: True if on.
        """
        return self.__config.get_value(GrammalecteConfig.AUTO_ANALYZE_ACTIVE) \
            and not self.is_readonly()

    def is_readonly(self) -> bool:
        """
        Indicate if the associated document is read-only.

        :return: True if editable.
        """
        return not self.view.get_editable()

    def get_config(self) -> GrammalecteConfig:
        """
        Return the configuration used for this document.
        """
        return self.__config


def get_view(view: Gtk.TextView) -> Optional[GrammalecteView]:
    """
    :return: The grammalecte view associated to the given view, may be none.
    """
    return _views.get(view)
