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

try:
    from .view import GrammalecteView
    from .window import GrammalecteWindow
    from .application import GrammalecteApplication

    import gi
    gi.require_version('Gedit', '3.0')
    gi.require_version('Gtk', '3.0')
except:
    print("Unable to load plugin — should be in test mode")
