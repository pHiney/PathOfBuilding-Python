"""
Configuration Class

Read, Writes and manages the settings xml as well as the settings therein
As the settings.xml can be altered by humans, care must be taken to ensure data integrity, where possible

This is a base PoB class. It doesn't import any other PoB ui classes
"""

from copy import deepcopy
from pathlib import Path
import os
import tempfile

from PySide6.QtCore import QSize, Slot

from PoB.pob_file import read_json, write_json
from PoB.constants import ColourCodes, pob_debug, def_theme, default_settings, empty_settings, locale
from PoB.utils import html_colour_text, str_to_bool, PoBDict

from dialogs.settings_dialog import SettingsDlg


class Settings(PoBDict):
    def __init__(self, _win, _app) -> None:
        """Init"""

        super().__init__(empty_settings)

        self._pob_debug = pob_debug
        # If called from a script, this will be none.
        if _app is None:
            return
        # To reduce circular references, have the app and main window references here
        self._win = _win
        self._app = _app
        self._screen_rect = self._app.primaryScreen().size()
        self._qss_background = "32, 33, 36, 1.000"
        self._qss_default_text = "#FFFFFF"

        # self.PoB: PoBDict = PoBDict(empty_settings)
        self.reset()

        # this is the xml tree representing the xml
        # self.root = None
        # self.tree = None
        # easy access to the Misc tag
        # self.misc = None
        # self.pastebin = None

        # Path and directory variables
        self._exe_dir = Path.cwd()
        self._extracted_dir = (
            "NUITKA_ONEFILE_PARENT" in os.environ
            and Path(tempfile.gettempdir(), f"PoB_{os.environ['NUITKA_ONEFILE_PARENT']}")
            or self._exe_dir
        )
        self._data_dir = Path(self._extracted_dir, "data")
        self._settings_file = Path(self._exe_dir, "settings.json")
        self.read()
        if self.build_path == "":
            self.build_path = str(Path(self._exe_dir, "builds"))
        if not Path(self.build_path).exists():
            try:
                Path(self.build_path).mkdir()
            except FileNotFoundError:
                print(f"Error: Failed to create '{self.build_path}' ...")
                self.build_path = str(Path(self._exe_dir, "builds"))
                if not Path(self.build_path).exists():
                    try:
                        print(f"   ... trying to create '{self.build_path}' again ...")
                        Path(self.build_path).mkdir()
                    except FileNotFoundError:
                        print(f"Error: Failed to create '{self.build_path}' for the second time. Giving up.")
                        # ignore it and hope for the best, cause there is something really wrong (eg: read-only filesystem)
                        pass

    def reset(self):
        """Reset to default config"""
        self.load(empty_settings)
        # self.tree = ET.ElementTree(ET.fromstring(default_settings))
        # self.root = self.tree.getroot()
        # self.misc = self.root.find("Misc")
        # self.pastebin = self.root.find("Misc")

    def read(self):
        """Set self.root with the contents of the settings file"""
        self.reset()
        if self._settings_file.exists():
            settings = read_json(self._settings_file)
            if settings:
                self.load(settings)

    def write(self):
        """Write the settings file"""
        write_json(self._settings_file, self.save())

    @property
    def qss_default_text(self):
        return self._qss_default_text

    @qss_default_text.setter
    def qss_default_text(self, new_colour):
        rgb = new_colour.split(",")
        self._qss_default_text = f"#{int(rgb[0]):x}{int(rgb[1]):x}{int(rgb[2]):x}"

    @property
    def pastebin_dev_api_key(self):
        try:
            return self.exists("pastebin") and self.pastebin.dev_api_key or ""
        except AttributeError:
            return ""

    @pastebin_dev_api_key.setter
    def pastebin_dev_api_key(self, new_key):
        if not self.exists("pastebin"):
            self.pastebin = PoBDict({})
        self.pastebin.dev_api_key = new_key

    @property
    def pastebin_user_api_key(self):
        try:
            return self.exists("pastebin") and self.pastebin.user_api_key or ""
        except AttributeError:
            return ""

    @pastebin_user_api_key.setter
    def pastebin_user_api_key(self, new_key):
        if not self.exists("pastebin"):
            self.pastebin = PoBDict({})
        self.pastebin.user_api_key = new_key

    @property
    def pastebin_user_name(self):
        try:
            return self.exists("pastebin") and self.pastebin.user_name or ""
        except AttributeError:
            return ""

    @pastebin_user_name.setter
    def pastebin_user_name(self, new_key):
        if not self.exists("pastebin"):
            self.pastebin = PoBDict({})
        self.pastebin.user_name = new_key

    # @property
    # def theme(self):
    #     return self.theme.lower()
    #
    # @theme.setter
    # def theme(self, new_theme):
    #     self.theme = new_theme.lower()

    # @property
    # def slot_only_tooltips(self):
    #     return str_to_bool(self.misc.get("slotOnlyTooltips", "True"))
    #
    # @slot_only_tooltips.setter
    # def slot_only_tooltips(self, new_bool):
    #     self.misc.set("slotOnlyTooltips", f"{new_bool}")

    # @property
    # def show_titlebar_name(self):
    #     return str_to_bool(self.misc.get("showTitlebarName", "True"))
    #
    # @show_titlebar_name.setter
    # def show_titlebar_name(self, new_bool):
    #     self.misc.set("showTitlebarName", f"{new_bool}")
    #
    # @property
    # def show_warnings(self):
    #     return str_to_bool(self.misc.get("showWarnings", "True"))
    #
    # @show_warnings.setter
    # def show_warnings(self, new_bool):
    #     self.misc.set("showWarnings", f"{new_bool}")

    # @property
    # def default_char_level(self):
    #     i = int(self.misc.get("defaultCharLevel", 0))
    #     if 1 <= i <= 100:
    #         return i
    #     self.default_char_level = 1
    #     return 1
    #
    # @default_char_level.setter
    # def default_char_level(self, new_level):
    #     self.misc.set("defaultCharLevel", f"{new_level}")

    # @property
    # def node_power_theme(self):
    #     i = int(self.misc.get("nodePowerTheme", 0))
    #     if 0 <= i <= 2:
    #         return i
    #     self.node_power_theme = 0
    #     return 0

    def node_power_theme_text(self):
        text = ["RED/BLUE", "RED/GREEN", "GREEN/BLUE"]
        return text[self.node_power_theme]

    # @node_power_theme.setter
    # def node_power_theme(self, new_theme):
    #     self.misc.set("nodePowerTheme", f"{new_theme}")

    # @property
    # def connection_protocol(self):
    #     i = int(self.misc.get("connectionProtocol", 0))
    #     if 0 <= i <= 2:
    #         return i
    #     self.connection_protocol = 0
    #     return 0
    #
    # @connection_protocol.setter
    # def connection_protocol(self, new_protocol):
    #     self.misc.set("connectionProtocol", f"{new_protocol}")
    #
    # @property
    # def decimal_separator(self):
    #     # ToDo: Use locale
    #     # c = self.misc.get("decimalSeparator", "")
    #     # if c = "":
    #     # use locale
    #     return self.misc.get("decimalSeparator", "_")
    #
    # @decimal_separator.setter
    # def decimal_separator(self, new_sep):
    #     self.misc.set("decimalSeparator", new_sep)
    #
    # @property
    # def thousands_separator(self):
    #     # ToDo: Use locale
    #     # c = self.misc.get("thousandsSeparator", "")
    #     # if c = "":
    #     # use locale
    #     return self.misc.get("thousandsSeparator", "n")
    #
    # @thousands_separator.setter
    # def thousands_separator(self, new_sep):
    #     self.misc.set("thousandsSeparator", new_sep)
    #
    # @property
    # def show_thousands_separators(self):
    #     return str_to_bool(self.misc.get("showThousandsSeparators", "True"))
    #
    # @show_thousands_separators.setter
    # def show_thousands_separators(self, new_bool):
    #     self.misc.set("showThousandsSeparators", f"{new_bool}")
    #
    # @property
    # def default_gem_quality(self):
    #     i = int(self.misc.get("defaultGemQuality", "0"))
    #     if 0 <= i <= 20:
    #         return i
    #     self.default_gem_quality = 0
    #     return 0
    #
    # @default_gem_quality.setter
    # def default_gem_quality(self, new_quality):
    #     self.misc.set("defaultGemQuality", f"{new_quality}")

    # @property
    # def build_sort_mode(self):
    #     return self.misc.get("buildSortMode", "NAME")
    #
    # @build_sort_mode.setter
    # def build_sort_mode(self, new_mode):
    #     self.misc.set("buildSortMode", new_mode)
    #
    # @property
    # def proxy_url(self):
    #     return self.misc.get("proxyURL", "")
    #
    # @proxy_url.setter
    # def proxy_url(self, new_proxy):
    #     self.misc.set("proxyURL", new_proxy)

    # @property
    # def default_item_affix_quality(self):
    #     """Aways store the number as a float between 0 and 1.00 so stats and items can call it correctly"""
    #     return float(self.misc.get("defaultItemAffixQuality", ".50"))
    #
    # @default_item_affix_quality.setter
    # def default_item_affix_quality(self, new_quality):
    #     """Aways store the number as a float between 0 and 1.00 so stats and items can call it correctly"""
    #     if new_quality < 0 or new_quality > 1.00:
    #         new_quality /= 100
    #     if new_quality < 0 or new_quality > 1.00:
    #         new_quality = 0.50
    #     self.misc.set("defaultItemAffixQuality", f"{new_quality}")

    # @property
    # def build_path(self):
    #     return self.misc.get("buildPath", "")
    #
    # @build_path.setter
    # def build_path(self, new_path):
    #     self.misc.set("buildPath", str(new_path))
    #
    # @property
    # def open_build(self):
    #     # If there was a build open when the program was last closed, which one was it.
    #     return self.misc.get("open_build", "")
    #
    # @open_build.setter
    # # If there was a build open when the program was last closed, which one was it.
    # def open_build(self, new_build):
    #     self.misc.set("open_build", new_build)

    # @property
    # def beta_mode(self):
    #     return str_to_bool(self.misc.get("betaMode", "False"))
    #
    # @beta_mode.setter
    # def beta_mode(self, new_bool):
    #     self.misc.set("betaMode", str(new_bool))

    @property
    def size(self):
        """
        Return the window size as they were last written to settings. This ensures the user has the same experience.
        800 x 600 was chosen as the default as it has been learnt, with the lua version,
          that some users in the world have small screen laptops.
        Attempt to protect against silliness by limiting size to the screen size.
          This could happen if someone changes their desktop size or copies the program from another machine.
        :returns: a QSize(width, height)
        """
        width = max(self.width, 800)
        height = max(self.height, 600)
        srw = self._screen_rect.width()
        if width > srw:
            print(f"Width: {width} is bigger than screen: {srw}. Correcting ...")
            width = srw
        srh = self._screen_rect.height()
        if height > srh:
            print(f"Height: {height} is bigger than screen: {srh}. Correcting ...")
            height = srh
        # self.size = QSize(width, height)
        return QSize(width, height)

    @size.setter
    def size(self, new_size: QSize):
        # _size = self.root.find("size")
        # _size.set("width", f"{new_size.width()}")
        # _size.set("height", f"{new_size.height()}")
        self.width = new_size.width()
        self.height = new_size.height()

    def get_recent_builds(self):
        """
        Recent builds are a list of build files that have been opened, to a maximum of 20 entries
        :returns: a list of recent builds
        """
        builds = self.recent_builds
        if builds is None:
            self.recent_builds = []
        else:
            builds = [fn for fn in self.recent_builds if Path(fn).exists()]
            self.recent_builds = builds[:20]
        return self.recent_builds

    def add_recent_build(self, filename):
        """
        Adds one build to the list of recent builds, moving an existing one to the front
        :param filename: string: name of build file
        :returns: bool: True if added to the list. False if already on the list.
        """
        # print(f"add_recent_build: {type(filename)=}, {filename=}")
        found = True
        try:
            self.recent_builds.remove(filename)
            self.recent_builds.insert(0, filename)
        except (IndexError, ValueError):
            found = False
            self.recent_builds.append(str(filename))
        return found

    # @property
    # def last_account_name(self):
    #     _accounts = self.root.find("Accounts")
    #     return _accounts.get("lastaccountName", "")
    #
    # @last_account_name.setter
    # def last_account_name(self, new_account_name):
    #     _accounts = self.root.find("Accounts")
    #     _accounts.set("lastaccountName", new_account_name)
    #
    # @property
    # def last_realm(self):
    #     _accounts = self.root.find("Accounts")
    #     return _accounts.get("lastRealm", "PC")
    #
    # @last_realm.setter
    # def last_realm(self, new_realm):
    #     _accounts = self.root.find("Accounts")
    #     _accounts.set("lastRealm", new_realm)

    # @property
    # def colour_negative(self):
    #     return self.misc.get("colour_negative", ColourCodes.NEGATIVE.value)
    #
    # @colour_negative.setter
    # def colour_negative(self, new_colour):
    #     self.misc.set("colour_negative", new_colour)
    #
    # @property
    # def colour_positive(self):
    #     return self.misc.get("colour_positive", ColourCodes.POSITIVE.value)
    #
    # @colour_positive.setter
    # def colour_positive(self, new_colour):
    #     self.misc.set("colour_positive", new_colour)
    #
    # @property
    # def colour_highlight(self):
    #     return self.misc.get("colour_highlight", ColourCodes.RED.value)
    #
    # @colour_highlight.setter
    # def colour_highlight(self, new_colour):
    #     self.misc.set("colour_highlight", new_colour)

    def accounts(self):
        """
        Recent accounts are a list of accounts that have been opened, to a maximum of 20 entries
        :returns: a list of recent accounts
        """
        accounts = self.accounts
        if accounts is None:
            self.accounts = []
        else:
            self.accounts = accounts[:20]
        return self.accounts

    def add_account(self, new_account):
        """
        Adds one account to the list of recent accounts, moving an existing one to the front.
        :param new_account: string: name of account
        :returns: bool: True if added to the list. False if already on the list.
        """
        found = True
        try:
            self.accounts.remove(new_account)
            self.accounts.insert(0, new_account)
        except (IndexError, ValueError):
            found = False
            self.accounts.append(new_account)
        return found

    @Slot()
    def open_settings_dialog(self):
        """
        Load and Open the settings dialog. Save the results if needed.
        :return:
        """
        # ToDo: show thousands separator for player stats

        dlg = SettingsDlg(self, self._win)
        loc = locale.localeconv()
        dlg.label_ThousandsSeparator.setText(f"{loc['thousands_sep']} {self._app.tr('and')} {loc['decimal_point']}")
        # 0 is discard, 1 is save
        _return = dlg.exec()
        if _return:
            dlg.save_settings()
            self.write()
        del dlg
