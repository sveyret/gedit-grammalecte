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

from gi.repository import Gedit, Gio, GObject, Gtk, PeasGtk

from .analyzer import GrammalecteAnalyzer
from .config import _
from .config_dlg import GrammalecteConfigDlg

_applications: Dict[Gtk.Application, 'GrammalecteApplication'] = {}


class GrammalecteApplication(GObject.Object, Gedit.AppActivatable, PeasGtk.Configurable):
    """
    The application activated part.
    """
    __gtype_name__ = "GrammalecteApplication"

    app: Gtk.Application = GObject.property(type=Gedit.App)

    def __init__(self) -> None:
        """
        Initialize the object.
        """
        GObject.Object.__init__(self)
        self.__analyzer: Optional[GrammalecteAnalyzer]
        self.__menu_ext = Gedit.MenuExtension

    def do_activate(self) -> None:
        """
        Called when application part of the plugin should be activated.
        """
        self.__analyzer = GrammalecteAnalyzer()
        self.__menu_ext = self.extend_menu("spell-section")
        self.__menu_ext.append_menu_item(Gio.MenuItem.new(
            _('Configure _Grammalecte...'), "win.ConfigGrammalecte"))
        self.__menu_ext.append_menu_item(Gio.MenuItem.new(
            _('Linguistic _Autocheck'), "win.AutoGrammalecte"))
        _applications[self.app] = self

    def do_deactivate(self) -> None:
        """
        Called when application part of the plugin should be deactivated.
        """
        if _applications.get(self.app) == self:
            del _applications[self.app]
        self.__menu_ext = None
        if self.__analyzer:
            self.__analyzer = None

    def do_update_state(self):
        pass

    def do_create_configure_widget(self) -> Gtk.Widget:
        """
        Create the global configuration widget.
        :return: The created widget.
        """
        return GrammalecteConfigDlg().get_widget()

    def get_analyzer(self) -> GrammalecteAnalyzer:
        """
        :return: The analyzer.
        """
        if self.__analyzer:
            return self.__analyzer
        else:
            raise Exception("Plugin does not seem to be properly initialized!")


def get_application(app: Gtk.Application) -> Optional[GrammalecteApplication]:
    """
    :return: The grammalecte application associated to the given application, may be none.
    """
    return _applications.get(app)
