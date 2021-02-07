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

from typing import Any, Dict, Optional, Union

import json
import os

from gi.repository import GLib, GObject


class SelfConfigContainer:
    """
    An object containing its configuration.

    A class inheriting from this one should manage itself the storage of its
    configuration (as a JSON string). This is useful for example for an object
    managing file metadata.
    """

    EMPTY = "{}"

    def get_self_config(self) -> str:
        """
        Get the configuration of the object.

        The configuration is a string parsable in JSON.

        :return: the configuration of the object.
        """
        pass

    def set_self_config(self, config: str) -> None:
        """
        Set the configuration of the object.

        The configuration is a string parsable in JSON.

        :param config: the configuration of the object.
        """
        pass


class DictConfig(GObject.GObject):
    """
    A configuration stored as a dictionnary.

    The configuration can be initialized with a dictionnary or with a JSON
    formatted file. In the latter case, modifications made to the configuration
    will be saved to the file. The file storage may be managed by an external
    object, useful for example to store the configuration in a document
    metadata.

    The configuration can have a parent, which is used when a value in child is
    None for a given path.

    Configuration values are accessed throw xPath-like definition.
    """
    __gtype_name__ = "DictConfig"
    __gsignals__ = {
        "updated": (GObject.SignalFlags.RUN_LAST, None, (int, str, object)),
        "cleared": (GObject.SignalFlags.RUN_LAST, None, (int,))
    }

    def __init__(self, data: Optional[Union[str, Dict[str, Any], SelfConfigContainer]], parent: Optional["DictConfig"] = None) -> None:
        """
        Initialize the instance.

        :param data: either the initialization dict for read-only, or the full
        name (including path) to the file where configuration is read.
        :param parent: (optional) the parent to use if configuration option is
        not found in current configuration.
        """
        GObject.GObject.__init__(self)

        self.__filedef: Optional[Union[str, SelfConfigContainer]]
        self.__config: Dict[str, Any]

        if data is None:
            self.__init_config({})
        elif isinstance(data, str):
            self.__init_file(data)
        elif isinstance(data, dict):
            self.__init_config(data)
        elif isinstance(data, SelfConfigContainer):
            self.__init_self_config(data)
        else:
            raise AttributeError

        self.__dirty: bool = False

        self.__parent = parent
        if self.__parent is not None:
            self.__eventUpdatedId: int = \
                self.__parent.connect("updated", self.on_updated)
            self.__eventClearedId: int = \
                self.__parent.connect("cleared", self.on_cleared)

    def __init_file(self, filename: str) -> None:
        """
        Initialize the instance with a file.

        :param filename: the full name of the file.
        """
        self.__filedef = filename
        self.__config = {}
        try:
            if os.path.exists(self.__filedef):
                with open(self.__filedef, 'r') as cfile:
                    self.__config = json.loads(cfile.read())
        except:
            pass

    def __init_config(self, config: Dict[str, Any]) -> None:
        """
        Initialize the instance with configuration.

        :param config: the read-only configuration.
        """
        self.__filedef = None
        self.__config = config

    def __init_self_config(self, selfConfig: SelfConfigContainer) -> None:
        """
        Initialize the instance with a self config container.

        :param selfConfig: the object.
        """
        self.__filedef = selfConfig
        self.__config = {}
        try:
            self.__config = json.loads(self.__filedef.get_self_config())
        except:
            pass

    def __del__(self) -> None:
        """
        Delete the configuration object.
        """
        if self.__parent is not None:
            self.__parent.disconnect(self.__eventUpdatedId)
            self.__parent.disconnect(self.__eventClearedId)
        self.__parent = None
        self.__config = {}
        self.__filedef = None

    def on_updated(self, _, level: int, xPath: str, newValue: Any) -> None:
        """
        Manage the updated event comming from parent.
        """
        self.emit("updated", level + 1, xPath, newValue)

    def on_cleared(self, _, level: int) -> None:
        """
        Manage the cleared event comming from parent.
        """
        self.emit("cleared", level + 1)

    def get_all_values(self, xPath: str) -> Any:
        """
        Get and concatenate the values corresponding to the given xPath.

        The values are first searched in the current configuration, then in
        parent configurations. All parent values not in current configuration
        are append to the value of the current configuration.

        Only list values can be concatenated. Top-most parent must have the
        value set (at least to an empty list).

        :param xPath: the xPath-like query to reach the values.
        :return: the values at matching position.
        """
        result = self.__find(xPath)
        if self.__parent is not None:
            pResult = self.__parent.get_all_values(xPath)
            if result is None:
                result = pResult
            elif not isinstance(result, list):
                raise AttributeError
            for key in pResult:
                if key not in result:
                    result.append(key)
        return result

    def get_value(self, xPath: str) -> Any:
        """
        Get the value corresponding to the given xPath.

        If no entry is found associated to the given xPath, the method recurse
        to the parent configuration, if available. If neither a value is found
        nor a parent defined, it will return None.

        :param xPath: the xPath-like query to reach the value.
        :return: the value at matching position, or None.
        """
        result = self.__find(xPath)
        if result is None and self.__parent is not None:
            result = self.__parent.get_value(xPath)
        elif isinstance(result, dict) and self.__parent is not None:
            result = {}
            for key in self.__get_keys(xPath):
                result[key] = self.get_value(xPath + "/" + key)
        return result

    def __get_keys(self, xPath: str) -> Any:
        """
        Get all the keys in the dict at xPath location.

        If the object at given location is not a dict, the key set will be
        empty.

        :param xPath: the xPath-like query to reach the dict.
        :return: a set of keys, or an empty set if no key.
        """
        keys = set()
        if self.__parent is not None:
            keys.update(self.__parent.__get_keys(xPath))
        value = self.__find(xPath)
        if isinstance(value, dict):
            for key in value:
                keys.add(key)
        return keys

    def add_value(self, xPath: str, value: Any, level: int = 0) -> None:
        """
        Add the value at the given xPath.

        If the path to the value does not exist, it is created, unless it is a
        list. The update is made on the parent at given level. A level of 0
        means to modify this configuration, 1 is for this parent's
        configuration, 2 is for this grand-parent's, etc.

        The xPath must point to a list. If there is no value for the given
        xPath, a new empty list is created. The given value is added to the
        list.

        :param xPath: the xPath-like query to reach the value.
        :param value: the value to add at given position.
        :param level: (optional) the parent level.
        """
        if level == 0:
            currentValue = self.__find(xPath)
            if currentValue is None:
                currentValue = []
            elif not isinstance(currentValue, list):
                raise AttributeError
            if value not in currentValue:
                newValue = list(currentValue)
                newValue.append(value)
                self.set_value(xPath, newValue)
        elif self.__parent is not None:
            self.__parent.add_value(xPath, value, level - 1)

    def del_value(self, xPath: str, value: Any, level: int = 0) -> None:
        """
        Delete the value from the given xPath.

        The update is made on the parent at given level. A level of 0 means to
        modify this configuration, 1 is for this parent's configuration, 2 is
        for this grand-parent's, etc.

        If the value exist, the xPath must point to a list. If there is a value
        for the given xPath, the given value is removed from the list.

        :param xPath: the xPath-like query to reach the value.
        :param value: the value to remove from given position.
        :param level: (optional) the parent level.
        """
        if level == 0:
            currentValue = self.__find(xPath)
            if currentValue is not None:
                if not isinstance(currentValue, list):
                    raise AttributeError
                newValue = list(currentValue)
                newValue.remove(value)
                self.set_value(xPath, newValue)
        elif self.__parent is not None:
            self.__parent.del_value(xPath, value, level - 1)

    def set_value(self, xPath: str, newValue: Any, level: int = 0) -> None:
        """
        Update the value corresponding to the given xPath.

        If the path to the value does not exist, it is created, unless it is a
        list. The update is made on the parent at given level. A level of 0
        means to modify this configuration, 1 is for this parent's
        configuration, 2 is for this grand-parent's, etc.

        :param xPath: the xPath-like query to reach the value.
        :param newValue: the new value to set at given position.
        :param level: (optional) the parent level.
        """
        if level == 0:
            if self.__find(xPath) != newValue:
                self.__update(xPath, newValue)
                self.__dirty = True
                self.emit("updated", 0, xPath, newValue)
        elif self.__parent is not None:
            self.__parent.set_value(xPath, newValue, level - 1)

    def __find(self, xPath: str) -> Any:
        """
        Find the value corresponding to the given xPath.

        Returns None if no entry is found associated to the given xPath, without
        searching in parents.

        :param xPath: the xPath-like query to reach the value.
        :return: the value at matching position, or None.
        """
        value: Any = self.__config
        try:
            for name in xPath.strip("/").split("/"):
                try:
                    name = int(name)  # type: ignore
                except ValueError:
                    pass
                value = value[name]
        except:
            value = None

        return value

    def __update(self, xPath: str, newValue: Any) -> None:
        """
        Update the value corresponding to the given xPath.

        If the path to the value does not exist, it is created, unless it is a
        list.

        :param xPath: the xPath-like query to reach the value.
        :param newValue: the new value to set at given position.
        """
        entry: Dict[Union[str, int], Any] = self.__config  # type: ignore
        oldName: Optional[Union[str, int]] = None
        try:
            for name in xPath.strip("/").split("/"):
                try:
                    name = int(name)  # type: ignore
                except ValueError:
                    pass
                if oldName is not None:
                    if not oldName in entry:
                        entry[oldName] = {}
                    entry = entry[oldName]
                oldName = name
            if oldName is not None:
                if newValue is None:
                    del entry[oldName]
                else:
                    entry[oldName] = newValue
        except:
            pass

    def clear(self, level: int = 0) -> None:
        """
        Clear all the configuration.

        All the parameters are removed from this configuration. The removal is
        made on the parent at given level. A level of 0 means to modify this
        configuration, 1 is for this parent's configuration, 2 is for this
        grand-parent's, etc.

        :param level: (optional) the parent level.
        """
        if level == 0:
            self.__config = {}
            self.emit("cleared", 0)
        elif self.__parent is not None:
            self.__parent.clear(level - 1)

    def save(self) -> None:
        """
        Save this configuration and the parents.

        If there are modifications and the configuration is associated to a
        valid file, it will be saved to disk.
        """
        if self.__parent is not None:
            self.__parent.save()
        if self.__filedef is not None and self.__dirty:
            if isinstance(self.__filedef, str):
                self.__save_file(self.__filedef)
            else:
                self.__save_self_config(self.__filedef)

    def __save_file(self, filename: str) -> None:
        """
        Save configuration as file.
        """
        try:
            configDir = os.path.dirname(filename)
            if not os.path.isdir(configDir):
                os.makedirs(configDir)
            with open(filename, 'w') as cfile:
                json.dump(self.__config, cfile, indent=2)
            self.__dirty = False
        except:
            print(_("Error: configuration file “{}” could not be saved")
                  .format(filename))

    def __save_self_config(self, container: SelfConfigContainer) -> None:
        """
        Save configuration as metadata.
        """
        try:
            container.set_self_config(json.dumps(
                self.__config, separators=(",", ":")))
        except:
            print(_("Error: configuration could not be saved"))


class GrammalecteConfig(DictConfig):
    """
    A Grammalecte configuration for a given document.

    This configuration inherits from user and system configuration, if
    available.

    :Example:

    >>> config = GrammalecteConfig()

    >>> config.get_value(GrammalecteConfig.ANALYZE_WAIT_TICKS)
    12

    >>> config.set_value("top/sub", ["zero", {"1st": "1", "other": "yes"}])

    >>> config.get_value("top/sub/1/other")
    'yes'
    """
    __gtype_name__ = "GrammalecteConfig"

    ############
    # ALL CONFIGURATION CONSTANTS ARE HERE
    ############
    LOCALE_DIR = "locale-dir"
    ANALYZE_OPTIONS = "analyze-options"
    AUTO_ANALYZE_ACTIVE = "auto-analyze-active"
    ANALYZE_PARALLEL_COUNT = "analyze-parallel-count"
    ANALYZE_WAIT_TICKS = "analyze-wait-ticks"
    IGNORED_RULES = "ign-rules"
    IGNORED_ERRORS = "ign-errors"
    CONCAT_LINES = "concat-lines"

    __DEFAULT_CONFIG = {
        ANALYZE_OPTIONS: {},
        AUTO_ANALYZE_ACTIVE: False,
        ANALYZE_PARALLEL_COUNT: 1,
        ANALYZE_WAIT_TICKS: 12,
        IGNORED_RULES: [],
        IGNORED_ERRORS: [],
        CONCAT_LINES: True,
    }

    __GEDIT_CONFIG_FILE = "/gedit/grammalecte.conf"
    __SYSTEM_CONFIG_FILE = "/etc" + __GEDIT_CONFIG_FILE
    __USER_CONFIG_FILE = GLib.get_user_config_dir() + __GEDIT_CONFIG_FILE

    __globalInstance: Optional[DictConfig] = None

    def __init__(self, selfConfig: Optional[SelfConfigContainer] = None) -> None:
        """
        Initialize the plugin configuration.

        :param selfConfig: (optional) the selfConfig container.
        """
        # Initialize global instance
        if GrammalecteConfig.__globalInstance is None:
            defaultConfig = DictConfig(GrammalecteConfig.__DEFAULT_CONFIG)
            systemConfig = DictConfig(
                GrammalecteConfig.__SYSTEM_CONFIG_FILE, defaultConfig)
            GrammalecteConfig.__globalInstance = DictConfig(
                GrammalecteConfig.__USER_CONFIG_FILE, systemConfig)

        # Initialize local instance
        DictConfig.__init__(
            self, selfConfig, GrammalecteConfig.__globalInstance)

    @staticmethod
    def terminate() -> None:
        """
        Terminate usage of all configurations.

        This will save global configuration files if needed.
        """
        if GrammalecteConfig.__globalInstance is not None:
            GrammalecteConfig.__globalInstance.save()
            GrammalecteConfig.__globalInstance = None


try:
    import gettext
    gettext.bindtextdomain(
        "gedit-grammalecte", localedir=GrammalecteConfig().get_value(GrammalecteConfig.LOCALE_DIR))
    gettext.textdomain("gedit-grammalecte")
    _ = gettext.gettext
except:
    def _(s): return s
