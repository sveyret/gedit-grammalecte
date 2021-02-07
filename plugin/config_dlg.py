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

from typing import Dict, List, Optional, Tuple

from grammalecte import GrammarChecker

from gi.repository import Gtk

from .config import GrammalecteConfig, _
from .error import GrammalecteError


class _Option:
    """
    An option of the plugin.
    """

    def __init__(self, identifier: str, value: bool, description: Optional[str], tooltip: Optional[str] = None) -> None:
        """
        Initialize the new option.

        :param identifier: The option identifier.
        :param value: The default value of the option.
        :param description: The description of the option.
        :param tooltip: The tooltip of the option.
        """
        if not description:
            description = identifier
        self.identifier: str = identifier
        self.button: Gtk.CheckButton = Gtk.CheckButton(description)
        self.button.set_active(value)
        self.button.set_tooltip_text(tooltip if tooltip else description)
        self.__config: Optional[Dict[str, bool]] = None
        self.__eventToggleId = self.button.connect("toggled", self.on_toggle)

    def terminate(self) -> None:
        """
        Terminate usage of the option.
        """
        self.button.disconnect(self.__eventToggleId)

    def link_config(self, config: Dict[str, bool]) -> None:
        """
        Link the button to the configuration, only for global configuration.

        :param config: The configuration items.
        """
        self.__config = config

    def on_toggle(self, button: Gtk.CheckButton) -> None:
        """
        Manage the toggle button event.

        :param button: The button.
        """
        if self.__config is not None:
            self.__config[self.identifier] = button.get_active()
            GrammalecteConfig().set_value(GrammalecteConfig.ANALYZE_OPTIONS, self.__config, 1)


class GrammalecteConfigDlg:
    """
    The configuration dialog. May be called from plugin configuration (for
    global configuration), or from a window (document-specific configuration).
    """
    __RESPONSE_CLEAR = 1
    __OPTION_ID = "id"
    __OPTION_BUTTON = "button"
    __OPTION_TOOLTIP = "tooltip"
    __OPTION_VALUE = "value"

    def __init__(self) -> None:
        """
        Prepare the dialog box.
        """
        self.__options: List[_Option] = []
        self.__optionsById: Dict[str, _Option] = {}
        self.__box: Gtk.VBox

        # Read options
        checker: GrammarChecker = GrammarChecker("fr")
        options: Dict[str, bool] = checker.getGCEngine().getOptions()
        labels: Dict[str, Tuple[str, str]
                     ] = checker.getGCEngine().getOptionsLabels()
        for identifier, value in options.items():
            label = labels.get(identifier)
            self.__options.append(_Option(
                identifier, value, label[0] if label else None, label[1] if label else None))

        # Terminate preparation
        self.__box = Gtk.VBox()
        for option in self.__options:
            self.__optionsById[option.identifier] = option
            self.__box.add(option.button)
        self.__box.connect("destroy", self.on_destroy)

    def get_widget(self) -> Gtk.VBox:
        """
        Get the widget for global configuration.
        """
        config = GrammalecteConfig()
        self.__apply_config(config)
        for option in self.__options:
            option.link_config(config.get_value(
                GrammalecteConfig.ANALYZE_OPTIONS))
        return self.__box

    def run_dialog(self, parent: Gtk.Window, config: GrammalecteConfig) -> None:
        """
        Run the dialog for local (document) configuration.

        :param parent: The parent window, containing the document.
        :param config: The configuration of the document.
        """
        # Create dialog
        dialog = Gtk.Dialog(_("Configuration"),
                            parent,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CLEAR, GrammalecteConfigDlg.__RESPONSE_CLEAR,
                             Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        dialog.connect('delete-event', self.on_delete_event)
        dialog.set_default_size(450, 400)

        # Manage clear button
        for button in dialog.get_action_area().get_children():
            if button.get_label() == "gtk-clear":
                button_clear = button
        if button_clear is None:
            raise Exception(_("Internal error"))
        button_clear.set_tooltip_text(_("Clear all file specific settings"))

        # Add options
        self.__apply_config(config)
        scrollBox = Gtk.ScrolledWindow()
        scrollBox.set_policy(Gtk.PolicyType.AUTOMATIC,
                             Gtk.PolicyType.AUTOMATIC)
        scrollBox.add_with_viewport(self.__box)
        scrollBox.set_propagate_natural_width(True)
        scrollBox.set_propagate_natural_height(True)
        dialog.get_content_area().add(scrollBox)

        # Run
        dialog.show_all()
        response = GrammalecteConfigDlg.__RESPONSE_CLEAR
        while response == GrammalecteConfigDlg.__RESPONSE_CLEAR:
            response = dialog.run()
            if response == GrammalecteConfigDlg.__RESPONSE_CLEAR:
                self.__clear_config(config)
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            self.__save_config(config)

    def __clear_config(self, config: GrammalecteConfig) -> None:
        """
        Clear the document configuration.

        :param config: The configuration to update.
        """
        autoAnalyze = config.get_value(GrammalecteConfig.AUTO_ANALYZE_ACTIVE)
        config.clear()
        config.set_value(GrammalecteConfig.AUTO_ANALYZE_ACTIVE, autoAnalyze)
        self.__apply_config(config)

    def __apply_config(self, config: GrammalecteConfig) -> None:
        """
        Apply the configuration to the check box.

        :param config: The configuration to update.
        """
        option_config: Dict[str, bool] = config.get_value(
            GrammalecteConfig.ANALYZE_OPTIONS)
        for option in self.__options:
            if option.identifier in option_config:
                option.button.set_active(option_config[option.identifier])

    def __save_config(self, config: GrammalecteConfig) -> None:
        """
        Save the local configuration.

        :param config: The configuration.
        """
        saved_config = {}
        global_config = GrammalecteConfig().get_value(GrammalecteConfig.ANALYZE_OPTIONS)
        for option in self.__options:
            value = option.button.get_active()
            if option.identifier not in global_config or global_config[option.identifier] != value:
                saved_config[option.identifier] = option.button.get_active()
        config.set_value(GrammalecteConfig.ANALYZE_OPTIONS, saved_config)

    def on_delete_event(self, dialog: Gtk.Dialog, event) -> None:
        """
        Dialog box was manually closed (cancel).
        """
        dialog.destroy()

    def on_destroy(self, box: Gtk.VBox) -> None:
        """
        Destroy the box, save the configuration if global.

        :param box: The box being destroyed.
        """
        for option in self.__options:
            option.terminate()
