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

from typing import List, Tuple

import subprocess

from gi.repository import Gtk

from .config import GrammalecteConfig, _
from .error import GrammalecteError


class CorrectionProcess():
    """
    Interface to be implemented by the correction process.
    """

    def convert_limits(self, position: Tuple[int, int], buffer: Gtk.TextBuffer) -> Gtk.TextIter:
        """
        Convert the limits provided by the error on the buffer to TextIter.

        :param position: The position of the error.
        :param buffer: The text buffer.
        :return: The text iterator for the position.
        """
        pass

    def get_config(self) -> GrammalecteConfig:
        """
        Get the configuration used by the correction process.

        :return: The configuration.
        """
        pass

    def get_buffer(self) -> Gtk.TextBuffer:
        """
        Get the current buffer being processed.

        :return: The buffer.
        """
        pass


class GrammalectePopupMenu():
    """
    Create and manage the popup menu related to an error.
    """

    def __init__(self, menu: Gtk.Menu, error: GrammalecteError, process: CorrectionProcess) -> None:
        """
        Create the menu options.

        :param menu: The menu to populate.
        :param error: The error related to the menu.
        :param process: The correction process.
        """
        menu_item = Gtk.SeparatorMenuItem()
        menu_item.show()
        menu.prepend(menu_item)
        menu_item = Gtk.ImageMenuItem(Gtk.STOCK_SPELL_CHECK)
        menu_item.set_label(_("Suggestions"))
        menu_item.set_submenu(self.build_suggestion_menu(error, process))
        menu_item.show_all()
        menu.prepend(menu_item)

    def build_suggestion_menu(self, error: GrammalecteError, process: CorrectionProcess) -> Gtk.Menu:
        """
        Build the suggestion menu.

        :param error: The error with suggestions.
        :param process: The correction process.
        :return: The suggestion menu.
        """
        suggestion_menu = Gtk.Menu()
        self.add_suggestions(suggestion_menu, error, process)
        self.add_actions(suggestion_menu, error, process.get_config())
        return suggestion_menu

    def add_suggestions(self, topmenu: Gtk.Menu, error: GrammalecteError, process: CorrectionProcess) -> None:
        """
        Add the actions to the suggestion menu.

        :param topmenu: The top suggestion menu.
        :param error: The error with suggestions.
        :param process: The correction process.
        """
        # Suggestions per groups of 6 items max
        suggestions = error.suggestions
        if len(suggestions) == 0:
            menu_item = Gtk.MenuItem(_("(no suggestions)"))
            menu_item.set_sensitive(False)
            menu_item.show_all()
            topmenu.append(menu_item)
        else:
            menu = topmenu
            count = 0
            for suggestion in suggestions:
                if count == 6:
                    menu_item = Gtk.SeparatorMenuItem()
                    menu_item.show()
                    menu.append(menu_item)
                    menu_item = Gtk.MenuItem(_("More"))
                    menu_item.show_all()
                    menu.append(menu_item)
                    menu = Gtk.Menu()
                    menu_item.set_submenu(menu)
                    count = 0
                menu_item = Gtk.MenuItem(suggestion)
                menu_item.show_all()
                menu.append(menu_item)
                menu_item.connect(
                    "activate", self.on_menu_replace, error, suggestion, process)
                count += 1

    def add_actions(self, suggestion_menu: Gtk.Menu, error: GrammalecteError, config: GrammalecteConfig) -> None:
        """
        Add the actions to the suggestion menu.

        :param suggestion_menu: The suggestion menu.
        :param error: The error with suggestions.
        :param config: The configuration of the correction process.
        """
        # Separator
        menu_item = Gtk.SeparatorMenuItem()
        menu_item.show()
        suggestion_menu.append(menu_item)

        # Ignore rule
        menu_item = Gtk.MenuItem(_("Ignore rule"))
        menu_item.set_sensitive(error.rule)
        menu_item.show_all()
        suggestion_menu.append(menu_item)
        menu_item.connect("activate", self.on_menu_ign_rule,
                          error.rule, config)

        # Ignore error in the file
        menu_item = Gtk.MenuItem(_("Ignore error"))
        menu_item.show_all()
        suggestion_menu.append(menu_item)
        menu_item.connect("activate", self.on_menu_ign_error,
                          list(error.context), config)

        # Add error to dictionnary
        menu_item = Gtk.MenuItem(_("Add"))
        menu_item.set_sensitive(error.option == GrammalecteError.SPELL_OPTION)
        menu_item.show_all()
        suggestion_menu.append(menu_item)
        menu_item.connect("activate", self.on_menu_add,
                          list(error.context), config)

        # Separator
        menu_item = Gtk.SeparatorMenuItem()
        menu_item.show()
        suggestion_menu.append(menu_item)

        # Open browser to see the rule
        menu_item = Gtk.MenuItem(_("See the rule"))
        menu_item.set_sensitive(error.url)
        menu_item.show_all()
        suggestion_menu.append(menu_item)
        menu_item.connect("activate", self.on_menu_info, error.url)

    def on_menu_replace(self, _, error: GrammalecteError, suggestion: str, process: CorrectionProcess) -> None:
        """
        Replace error with suggestion.

        :param error: The related error.
        :param suggestion: The string to use as replacement.
        :param process: The correction process.
        """
        text_buffer = process.get_buffer()
        start = process.convert_limits(error.start, text_buffer)
        end = process.convert_limits(error.end, text_buffer)
        oldText = text_buffer.get_slice(start, end, True)
        if oldText == error.context.erroneous:
            text_buffer.begin_user_action()
            text_buffer.delete(start, end)
            text_buffer.insert(start, suggestion)
            text_buffer.end_user_action()

    def on_menu_ign_rule(self, _, rule: str, config: GrammalecteConfig) -> None:
        """
        Ignore the rule in the file.

        :param rule: The name of the rule to ignore.
        :param config: The process configuration.
        """
        config.add_value(GrammalecteConfig.IGNORED_RULES, rule)

    def on_menu_ign_error(self, _, context: List[str], config: GrammalecteConfig) -> None:
        """
        Ignore the error in the file.

        :param context: The context, i.e. erroneous word and surrounding.
        :param config: The process configuration.
        """
        config.add_value(GrammalecteConfig.IGNORED_ERRORS, context)

    def on_menu_add(self, _, context: List[str], config: GrammalecteConfig) -> None:
        """
        Add the error to the dictionnary.

        :param context: The context, i.e. erroneous word and surrounding.
        :param config: The process configuration.
        """
        config.add_value(GrammalecteConfig.IGNORED_ERRORS, context, 1)

    def on_menu_info(self, _, url) -> None:
        """
        Open the URL.

        :param url: The URL to open for the rule.
        """
        subprocess.Popen(['xdg-open', url])
