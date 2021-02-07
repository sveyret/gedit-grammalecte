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

# Directories
TARGET_DIR=target
LOCALE_DIR=$(TARGET_DIR)/locale
PLUGIN_DIR=$(TARGET_DIR)/plugin

# Target directories
LOCALE_INSTALL ?= /usr/share/locale
PLUGIN_INSTALL ?= /usr/lib

# Application id
APP_TYPE=plugin
APP_PACKNAME=gedit-grammalecte
APP_VERSION=0.1
APP_AUTHOR=Stéphane Veyret

# Sources and targets
POS=$(wildcard po/*.po)
MOS=$(addsuffix /LC_MESSAGES/$(APP_PACKNAME).mo,$(addprefix $(LOCALE_DIR)/,$(notdir $(basename $(POS)))))
INI=plugin/$(APP_PACKNAME).$(APP_TYPE)
PYS=$(filter-out $(wildcard plugin/test_*.py),$(wildcard plugin/*.py))
BIN=$(addprefix $(PLUGIN_DIR)/,$(notdir $(INI))) $(addprefix $(PLUGIN_DIR)/$(APP_PACKNAME)/,$(notdir $(PYS)))

all: $(MOS) $(BIN)

po/$(APP_PACKNAME).pot:
	xgettext --package-name="$(APP_PACKNAME)" --package-version="$(APP_VERSION)" --copyright-holder="$(APP_AUTHOR)" -o "$@" -L Python plugin/*.py

%.po: po/$(APP_PACKNAME).pot
	[[ ! -f "$@" ]] || msgmerge -U "$@" "$<"
	[[ -f "$@" ]] || msginit -o "$@" -i "$<" -l "$(notdir $*)" --no-translator

%.mo: %.po
	msgfmt -o "$@" "$<"

$(LOCALE_DIR)/%/LC_MESSAGES/$(APP_PACKNAME).mo: po/%.mo
	mkdir -p "$(dir $@)"
	cp "$<" "$@"

$(PLUGIN_DIR)/%: plugin/%
	mkdir -p "$(dir $@)"
	cp "$<" "$@"

$(PLUGIN_DIR)/$(APP_PACKNAME)/%.py: plugin/%.py
	mkdir -p "$(dir $@)"
	cp "$<" "$@"

test:
	python -m unittest discover -s plugin -t .

install:
	install -d -m755 "$(DESTDIR)$(LOCALE_INSTALL)"
	cp -r $(LOCALE_DIR)/* "$(DESTDIR)$(LOCALE_INSTALL)"
	install -d -m755 "$(DESTDIR)$(PLUGIN_INSTALL)/gedit/plugins"
	cp -r $(PLUGIN_DIR)/* "$(DESTDIR)$(PLUGIN_INSTALL)/gedit/plugins"

clean:
	rm -f *~
	rm -f plugin/*.pyc
	rm -f plugin/*~
	rm -f po/*.mo
	rm -f po/*~

mrproper: clean
	rm -rf $(TARGET_DIR)

.PHONY: all check install clean mrproper

