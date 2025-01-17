"""
The owner of everything.
Builds are opened and saved from here.
Menus and the button/tool bar are owned and operated here.
The extra widgets on the button/tool bar are added here as the designer doesn't seem to be add them.
Functions that involve multi-tabs are here due to this class being their (eg: show_skillset, change_tree).
"""

import atexit
from copy import deepcopy
import datetime
import glob
import os
import platform
import pyperclip
import re
import subprocess
import sys

from typing import Union
from pathlib import Path
import psutil

from PySide6.QtCore import Qt, QPoint, QProcess, Slot
from PySide6.QtGui import QAction, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QToolButton,
    QWidget,
    QWidgetAction,
)

from PoB.constants import (
    ColourCodes,
    PlayerClasses,
    bandits,
    bad_text,
    def_theme,
    empty_gem_dict,
    pantheon_major_gods,
    pantheon_minor_gods,
    player_stats_list,
    pob_debug,
    program_title,
    resistance_penalty,
)

from PoB.build import Build
from PoB.settings import Settings
from PoB.pob_file import get_file_info
from PoB.player import Player
from PoB.utils import html_colour_text, format_number, is_str_a_number, print_call_stack, str_to_bool, _debug
from PoB.pob_xml import load_from_xml, save_to_xml
from dialogs.browse_file_dialog import BrowseFileDlg
from dialogs.export_dialog import ExportDlg
from dialogs.import_dialog import ImportDlg
from dialogs.popup_dialogs import yes_no_dialog
from widgets.calcs_ui import CalcsUI
from widgets.config_ui import ConfigUI
from widgets.flow_layout import FlowLayout
from widgets.items_ui import ItemsUI
from widgets.listbox import ListBox
from widgets.notes_ui import NotesUI
from widgets.player_stats import PlayerStats
from widgets.skills_ui import SkillsUI
from widgets.tree_ui import TreeUI
from widgets.tree_view import TreeView
from widgets.ui_utils import set_combo_index_by_data

from ui.PoB_Main_Window import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, _app) -> None:
        super(MainWindow, self).__init__()
        self.last_message = ""
        print(f"{datetime.datetime.now()}. {program_title}, running on {platform.system()} {platform.release()};" f" {platform.version()}")
        self.app = _app
        self.tr = self.app.tr
        self._os = platform.system()
        # self.loader = QUiLoader()
        # ToDo investigate if some settings need to be changed per o/s

        # When False stop all the images being deleted and being recreated
        self.refresh_tree = True
        self.triggers_connected = False

        # information from an imported character
        self.account_name = ""
        self.import_character_name = ""
        self.import_league = ""

        # The QAction representing the current theme (to turn off the menu's check mark)
        self.curr_theme = None

        # Flag to stop some actions happening in triggers during loading or changing tree Specs
        self.alerting = True

        self.max_points = 123
        self.settings = Settings(self, _app)

        self.setupUi(self)
        self.resize(self.settings.size)
        if self.settings.get("maximized", False):
            self.showMaximized()
        self.last_messages = []
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.check_clipboard_contents)

        atexit.register(self.exit_handler)
        self.setWindowTitle(program_title)  # Do not translate

        # Start with an empty build. This ensures there are values for widgets as they set themselves up.
        self.build = Build(self.settings, self)
        # self.current_filename = self.settings.build_path
        self.player = Player(self.settings, self.build, self)

        # Setup UI Classes()
        # self.stats = PlayerStats(self.settings, self)
        self.calcs_ui = CalcsUI(self.settings, self.build, self)
        self.config_ui = ConfigUI(self.settings, self.build, self)
        self.notes_ui = NotesUI(self.settings, self)
        # skills_ui before tree_ui and items_ui, as they need the hidden_skills.json loaded.
        self.skills_ui = SkillsUI(self.settings, self.build, self)
        # tree_ui before items_ui, as it needs 'open_manage_trees' function.
        self.tree_ui = TreeUI(self.settings, self.build, self.frame_TreeTools, self)
        self.items_ui = ItemsUI(self.settings, self.build, self.tree_ui, self)

        """
            Start: Do what the QT Designer cannot yet do 
        """
        # add widgets to the Toolbar
        widget_height = 24
        widget_spacer = QWidget()  # spacers cannot go into the toolbar, only Widgets
        widget_spacer.setMinimumSize(10, widget_height)
        # self.toolbar_MainWindow.insertWidget(self.action_Theme, widget_spacer)
        # widget_spacer = QWidget()
        # widget_spacer.setMinimumSize(50, 0)
        self.toolbar_MainWindow.addWidget(widget_spacer)
        self.label_points = QLabel(" 0 / 123  0 / 8 ")
        self.label_points.setMinimumSize(120, widget_height)
        self.label_points.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.toolbar_MainWindow.addWidget(self.label_points)
        self.label_level = QLabel("Level: ")
        self.label_level.setMinimumSize(60, widget_height)
        self.label_level.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.toolbar_MainWindow.addWidget(self.label_level)
        self.spin_level = QSpinBox()
        self.spin_level.setMinimum(1)
        self.spin_level.setMaximum(100)
        self.spin_level.setMinimumSize(10, widget_height)
        self.spin_level.setEnabled(False)
        self.toolbar_MainWindow.addWidget(self.spin_level)

        self.cb_level_auto_manual = QCheckBox("Manual", checked=False)
        self.cb_level_auto_manual.setMinimumSize(90, widget_height)
        self.cb_level_auto_manual.stateChanged.connect(self.cb_level_auto_manual_changed)
        self.toolbar_MainWindow.addWidget(self.cb_level_auto_manual)

        widget_spacer = QWidget()
        widget_spacer.setMinimumSize(100, widget_height)
        self.toolbar_MainWindow.addWidget(widget_spacer)

        self.combo_classes = QComboBox()
        self.combo_classes.setMinimumSize(100, widget_height)
        self.combo_classes.setDuplicatesEnabled(False)
        for idx in PlayerClasses:
            self.combo_classes.addItem(idx.name.title(), idx)
        self.toolbar_MainWindow.addWidget(self.combo_classes)
        widget_spacer = QWidget()
        widget_spacer.setMinimumSize(10, widget_height)
        self.toolbar_MainWindow.addWidget(widget_spacer)
        self.combo_ascendancy = QComboBox()
        self.combo_ascendancy.setMinimumSize(125, widget_height)
        self.combo_ascendancy.setDuplicatesEnabled(False)
        self.combo_ascendancy.addItem("None", 0)
        self.combo_ascendancy.addItem("Ascendant", 1)
        self.toolbar_MainWindow.addWidget(self.combo_ascendancy)

        widget_spacer = QWidget()
        widget_spacer.setMinimumSize(100, widget_height)
        self.toolbar_MainWindow.addWidget(widget_spacer)

        btn_calc = QPushButton("Do Calcs")
        btn_calc.clicked.connect(self.do_calcs)
        self.toolbar_MainWindow.addWidget(btn_calc)

        # end add widgets to the Toolbar

        # Dump the placeholder Graphics View and add our own
        # Cannot be set in TreeUI() init due to recursion error.
        self.gview_Tree = TreeView(self.settings, self.build, self)
        self.vlayout_tabTree.replaceWidget(self.graphicsView_PlaceHolder, self.gview_Tree)
        # destroy the old object
        self.graphicsView_PlaceHolder.setParent(None)
        # Copy the jewels list to tree_view so it can show jewels properly.
        # These two should point to the same pointer, so further updates through items_ui will update both.
        self.gview_Tree.items_jewels = self.items_ui.jewels

        # Add our FlowLayout to Config tab
        self.layout_config = FlowLayout(None, 0)
        self.frame_Config.setLayout(self.layout_config)
        self.layout_config.addItem(self.grpbox_General)
        self.layout_config.addItem(self.grpbox_Combat)
        self.layout_config.addItem(self.grpbox_SkillOptions)
        self.layout_config.addItem(self.grpbox_EffectiveDPS)
        self.layout_config.addItem(self.grpbox_5)
        self.layout_config.addItem(self.grpbox_CustomModifiers)
        print()

        # Configure basic Configuration setup
        self.config_ui.initial_startup_setup()

        # set the ComboBox dropdown width.
        self.combo_Bandits.view().setMinimumWidth(self.combo_Bandits.minimumSizeHint().width())

        """
            End: Do what the QT Designer cannot yet do 
        """

        self.toolbar_buttons = {}
        for widget in self.toolbar_MainWindow.children():
            # QActions are joined to the toolbar using QToolButtons.
            if type(widget) is QToolButton:
                self.toolbar_buttons[widget.toolTip()] = widget

        # Theme loading has to happen before creating more UI elements that use html_colour_text()
        self.setup_theme_actions()
        self.switch_theme(self.settings.theme, self.curr_theme)

        self.combo_ResPenalty.clear()
        for penalty in resistance_penalty.keys():
            self.combo_ResPenalty.addItem(resistance_penalty[penalty], penalty)
        self.combo_Bandits.clear()
        for idx, bandit_name in enumerate(bandits.keys()):
            bandit_info = bandits[bandit_name]
            self.combo_Bandits.addItem(bandit_info.get("name"), bandit_name)
            self.combo_Bandits.setItemData(
                idx,
                html_colour_text("TANGLE", bandit_info.get("tooltip")),
                Qt.ToolTipRole,
            )
        self.combo_MajorPantheon.clear()
        for idx, god_name in enumerate(pantheon_major_gods.keys()):
            god_info = pantheon_major_gods[god_name]
            self.combo_MajorPantheon.addItem(god_info.get("name"), god_name)
            self.combo_MajorPantheon.setItemData(idx, html_colour_text("TANGLE", god_info.get("tooltip")), Qt.ToolTipRole)
        self.combo_MinorPantheon.clear()
        for idx, god_name in enumerate(pantheon_minor_gods.keys()):
            god_info = pantheon_minor_gods[god_name]
            self.combo_MinorPantheon.addItem(god_info.get("name"), god_name)
            self.combo_MinorPantheon.setItemData(idx, html_colour_text("TANGLE", god_info.get("tooltip")), Qt.ToolTipRole)
        self.combo_EHPUnluckyWorstOf.addItem("Average", 1)
        self.combo_EHPUnluckyWorstOf.addItem("Unlucky", 2)
        self.combo_EHPUnluckyWorstOf.addItem("Very Unlucky", 4)
        self.combo_igniteMode.addItem("Average", "AVERAGE")
        self.combo_igniteMode.addItem("Crits Only", "CRIT")

        self.menu_Builds.addSeparator()
        self.set_recent_builds_menu_items()

        # Collect original tooltip text for Actions (for managing the text color thru qss - switch_theme)
        # Must be before the first call to switch_theme
        # file = "c:/git/PathOfBuilding-Python.sus/src/data/qss/material-blue.qss"
        # file = "c:/git/PathOfBuilding-Python.sus/src/data/qss/test_dark.qss"
        # with open(file, "r") as fh:
        #     QApplication.instance().setStyleSheet(fh.read())
        # Connect our Actions / triggers
        self.tab_main.currentChanged.connect(self.set_tab_focus)
        self.action_New.triggered.connect(self.build_new)
        self.action_Open.triggered.connect(self.build_open)
        self.action_Save.triggered.connect(self.build_save)
        self.action_SaveAs.triggered.connect(self.build_save_as)
        self.action_Settings.triggered.connect(self.settings.open_settings_dialog)
        self.action_Import.triggered.connect(self.open_import_dialog)
        self.action_Export.triggered.connect(self.open_export_dialog)
        self.statusbar_MainWindow.messageChanged.connect(self.update_status_bar)

        self.combo_Bandits.currentTextChanged.connect(self.display_number_node_points)
        self.combo_MainSkill.currentTextChanged.connect(self.main_skill_text_changed)
        self.combo_MainSkill.currentIndexChanged.connect(self.main_skill_index_changed)
        self.combo_MainSkillActive.currentTextChanged.connect(self.active_skill_changed)
        # self.

        # these two Manage Tree combo's are linked
        self.tree_ui.combo_manage_tree.currentTextChanged.connect(self.change_tree)
        self.combo_ItemsManageTree.currentTextChanged.connect(self.combo_item_manage_tree_changed)
        self.connect_widget_triggers()

        # Start the statusbar self updating
        self.update_status_bar()

        self.calc_process = None
        self.current_stats = []  # list of lines from the luajit. Used for future comparisons.
        # self.do_calcs()

        # init

    # Overridden function
    def keyReleaseEvent(self, event):
        """
        Handle key presses into the general application (outside a widget's focus).
         Mainly for Ctrl-V for pasting skill groups and items

        :param: QKeyEvent. The event matrix
        :return: N/A
        """
        ctrl_pressed = event.keyCombination().keyboardModifiers() == Qt.ControlModifier
        alt_pressed = event.keyCombination().keyboardModifiers() == Qt.AltModifier
        shift_pressed = event.keyCombination().keyboardModifiers() == Qt.ShiftModifier
        success = False
        active_widget = self.app.focusWidget()
        # print(f"MainWindow: {type(active_widget)=}", event)
        # if the action came from a edit widget, ignore the message and get outa here ...
        # if active_widget and active_widget.objectName() == "textedit_Notes":
        if active_widget and type(active_widget) in (QLineEdit, QTextEdit):
            event.ignore()
            super(MainWindow, self).keyPressEvent(event)
            return
        match event.key():
            case Qt.Key_C:
                if ctrl_pressed:
                    print(f"MainWindow: Ctrl-C pressed.")
                    if type(active_widget) is ListBox:
                        self.clipboard.dataChanged.connect(self.check_clipboard_contents)
                        match active_widget.objectName():
                            case "list_Items" | "list_ImportItems":
                                pyperclip.copy(self.items_ui.copy_item_as_text(active_widget))
                                event.accept()
                            case "list_SocketGroups":
                                pyperclip.copy(self.skills_ui.copy_sg_as_text(active_widget))
                                event.accept()
                            case "list_Skills":
                                # pyperclip.copy(self.items_ui.copy_item_as_text(active_widget))
                                event.accept()
                            case _:
                                event.ignore()
                        super(MainWindow, self).keyPressEvent(event)
                        self.clipboard.dataChanged.connect(self.check_clipboard_contents)
            case Qt.Key_V:
                if ctrl_pressed:
                    print(f"MainWindow: Ctrl-V pressed. {self.skills_ui.internal_clipboard=}, {self.items_ui.internal_clipboard=}")
                    data = pyperclip.paste()
                    if self.skills_ui.internal_clipboard or "slot:" in data:
                        self.set_tab_focus(1)
                        success = self.skills_ui.get_sg_from_clipboard(data)
                    elif "Rarity: Gem" in data:
                        self.set_tab_focus(1)
                        success = self.skills_ui.get_gem_from_clipboard(data)
                    elif self.items_ui.internal_clipboard:
                        self.set_tab_focus(2)
                        success = self.items_ui.get_item_from_clipboard()
                    else:
                        # Assume it is going to come from outside the application, ingame or trade site
                        data = pyperclip.paste()
                        print(f"MainWindow: Ctrl-V pressed. External Data: {type(data)=} {data=}")
                        if data is not None and type(data) is str:
                            if "Item Class: Skill Gems" in data:
                                success = self.skills_ui.get_gem_from_clipboard(data)
                            elif "Rarity" in data:
                                success = self.items_ui.get_item_from_clipboard(data)
                            elif "Slot:" in data:
                                success = self.skills_ui.get_sg_from_clipboard(data)
                        # match self.build.viewMode:
                        #     case "SKILLS":
                        #         self.skills_ui.get_item_from_clipboard()
                        #     case "ITEMS":
                        #         self.items_ui.get_item_from_clipboard()
                    if not success:
                        event.ignore()
        super(MainWindow, self).keyPressEvent(event)

    # Overridden function
    def moveEvent(self, e):
        # print(f"MainWindow moveEvent: {self.pos()=}")
        self.settings.pos = self.pos()
        super(MainWindow, self).moveEvent(e)

    def setup_ui(self):
        """Called after show(). Call setup_ui for all UI classes that need it"""
        self.items_ui.setup_ui()
        self.skills_ui.setup_ui()

        # Check to see if there is a previous build to load and load it here
        if self.settings.open_build:
            self.build_loader(self.settings.open_build)
        else:
            self.build_new()

    def connect_widget_triggers(self):
        """re-connect widget triggers that need to be disconnected during loading and other processing"""
        # print("connect_item_triggers", self.triggers_connected)
        # print_call_stack(idx=-4)
        if self.triggers_connected:
            # Don't re-connect
            return
        self.triggers_connected = True
        self.combo_classes.currentTextChanged.connect(self.class_changed)
        self.combo_ascendancy.currentTextChanged.connect(self.ascendancy_changed)

    def disconnect_widget_triggers(self):
        """disconnect widget triggers that need to be disconnected during loading and other processing"""
        # print("disconnect_item_triggers", self.triggers_connected)
        # print_call_stack(idx=-4)
        if not self.triggers_connected:
            # Don't disconnect if not connected
            return
        self.triggers_connected = False
        self.combo_classes.currentTextChanged.disconnect(self.class_changed)
        self.combo_ascendancy.currentTextChanged.disconnect(self.ascendancy_changed)

    def set_recent_builds_menu_items(self):
        """
        Setup menu entries for all valid recent builds in the settings file
        Read the config for recent builds and create menu entries for them
        return: N/A
        """

        def make_connection(_full_path):
            """
            Connect the menu item to _open_previous_build passing in extra information
            Lambdas in python share the variable scope they're created in so make a function containing just the lambda
            :param _full_path: full path to the file, to be sent to the triggered function.
            :return: N/A
            """
            _action.triggered.connect(lambda checked: self._open_previous_build(checked, _full_path))

        os.chdir(self.settings.build_path)
        max_length = 80
        recent_builds = self.settings.get_recent_builds()
        for idx, full_path in enumerate(recent_builds):

            if full_path is not None and full_path != "":
                text, class_name = get_file_info(self.settings, full_path, max_length, 70, menu=True)
                # print(f"set_recent_builds_menu_items: {class_name=}, {full_path=}")
                ql = QLabel(text)
                _action = QWidgetAction(self.menu_Builds)
                _action.setDefaultWidget(ql)
                self.menu_Builds.addAction(_action)
                make_connection(full_path)

    def add_recent_build_menu_item(self):
        """
        Add this file (either Open or Save As) to the recent menu list. refreshing the menu if the name is a new one.
        :return: N/A
        """
        # print(f"add_recent_build_menu_item: {self.build.filename=}")
        self.settings.add_recent_build(self.build.filename)
        for entry in self.menu_Builds.children():
            if type(entry) is QWidgetAction:
                self.menu_Builds.removeAction(entry)
        self.set_recent_builds_menu_items()

    def setup_theme_actions(self):
        """
        Dynamically create actions on the Theme menu and connect the action to switch_theme()
        :return: N/A
        """

        def make_connection(name, _action):
            """
            Connect the menu item to switch_theme passing in extra information.
            Lambdas in python share the variable scope they're created in
            so make a function containing just the lambda
            :param name: str; the name of the file but no extension.
            :param _action: QAction; the current action.
            :return: N/A
            """
            _action.triggered.connect(lambda checked: self.switch_theme(name, _action))

        themes = [os.path.basename(x) for x in glob.glob(f"{self.settings._data_dir}/qss/*.colours")]
        # print("setup_theme_actions", themes)
        for value in themes:
            _name = os.path.splitext(value)[0]
            action: QAction = self.menu_Theme.addAction(_name.title())
            action.setCheckable(True)
            if _name == self.settings.theme:
                self.curr_theme = action
                action.setChecked(True)
            make_connection(_name, action)

    def exit_handler(self):
        """
        Ensure the build can be saved before exiting if needed.
        Save the configuration to settings.xml. Any other activities that might be needed
        """
        self.settings.maximized = self.isMaximized()
        if not self.settings.maximized:
            # don't disturb the previous settings if you are maximized.
            self.settings.size = self.size()
        self.settings.write()
        # Logic for checking we need to save and save if needed, goes here...
        # filePtr = open("edit.html", "w")
        # try:
        #     filePtr.write(self.textedit_Notes.toHtml())
        # finally:
        #     filePtr.close()
        sys.stdout.close()

    @Slot()
    def cb_level_auto_manual_changed(self, checked):
        """

        :param checked: bool:
        :return: N/A
        """
        # print("cb_level_auto_manual_changed", checked)
        self.build.json_tree_view["level_auto_manual"] = checked
        self.spin_level.setEnabled(checked)
        self.estimate_player_progress()

    @Slot()
    # Do all actions needed to change between light and dark
    def switch_theme(self, new_theme, selected_action):
        """
        Set the new theme based on the name passed through.
        The text of the action has a capital letter but the filenames are lowercase.
        :param new_theme: str: A name of a theme file.
        :param selected_action: QAction: The object representing the selected manu item.

        :return: N/A
        """

        def set_colors(window_colour, text_colour):
            # colours = window_colour, text_colour
            # Setup the window Palette
            pal = self.window().palette()
            pal.setColor(QPalette.Window, QColor(f"#{window_colour}"))
            pal.setColor(QPalette.WindowText, QColor(text_colour))
            self.window().setPalette(pal)
            #
            # # Put in a small QSS
            # print(window_colour[0:2], int(window_colour[0:2], 16))
            # if int(f"0x{window_colour[0:2]}", 16) >= 128:
            #     print(window_colour, f"{int(window_colour, 16) - int(0x202020):x}")
            #     alt_colour = f"#{int(window_colour, 16) - int(0x101010):x}"
            #     hover_colour = f"#{int(text_colour, 16) - int(0x202020):x}"
            # else:
            #     print(window_colour, f"{int(window_colour, 16) + int(0x202020):x}")
            #     alt_colour = f"#{int(window_colour, 16) + int(0x101010):x}"
            #     hover_colour = f"#{int(text_colour, 16) + int(0x202020):x}"
            #
            # # put the # back on so the qss_template.format() doesn't error: KeyError: '404044'
            # window_colour = f"#{window_colour}"
            # text_colour = f"#{text_colour}"
            #
            # self.settings.qss_default_text = text_colour
            # qss = qss_template.format(**locals())
            # # print(qss)
            # QApplication.instance().setStyleSheet(qss)

        # set_colors

        # print(f"switch_theme, {new_theme=}, {self.curr_theme.text()=}")
        # if new_theme == "dark":
        #     set_colors("121218", "d6d6d6")
        # elif new_theme == "light":
        #     set_colors("f0f0f0", "404044")
        # elif new_theme == "blue":
        #     set_colors("cee7f0", "404044")
        # elif new_theme == "brown":
        #     set_colors("9e8965", "404044")
        # elif new_theme == "orange":
        #     set_colors("cc8800", "181818")
        # if self.curr_theme is not None:
        #     self.curr_theme.setChecked(False)
        # self.settings.theme = new_theme
        # self.curr_theme = selected_action
        # if self.curr_theme is not None:
        #     #     self.curr_theme.setChecked(False)
        #     self.curr_theme.setChecked(True)
        # return
        file = Path(self.settings._data_dir, "qss", f"{new_theme}.colours")
        new_theme = Path.exists(file) and new_theme or def_theme
        try:
            with open(Path(self.settings._data_dir, "qss", "qss.template"), "r") as template_file:
                template = template_file.read()
            with open(Path(self.settings._data_dir, "qss", f"{new_theme}.colours"), "r") as colour_file:
                colours = colour_file.read().splitlines()
                for line in colours:
                    line = line.split("~~")
                    if len(line) == 2:
                        if line[0] == "qss_background":
                            self.settings._qss_background = line[1]
                        if line[0] == "qss_default_text":
                            self.settings.qss_default_text = line[1]
                            for tooltip_text in self.toolbar_buttons.keys():
                                self.toolbar_buttons[tooltip_text].setToolTip(
                                    html_colour_text(self.settings.qss_default_text, tooltip_text)
                                )
                        template = re.sub(r"\b" + line[0] + r"\b", line[1], template)

            QApplication.instance().setStyleSheet(template)
            # Uncheck old entry. First time through, this could be None.
            if self.curr_theme is not None:
                self.curr_theme.setChecked(False)
            self.settings.theme = new_theme.lower()
            self.curr_theme = selected_action
            if self.curr_theme is not None:
                self.curr_theme.setChecked(True)
        # parent of IOError, OSError *and* WindowsError where available
        except (EnvironmentError, FileNotFoundError):
            print(f"Unable to open theme files.")

    @Slot()
    def close_app(self):
        """
        Trigger closing of the app. May not get used anymore as action calls MainWindow.close().
        Kept here in case it's more sensible to run 'close down' procedures in an App that doesn't yet know it's closing.
            In which case, change the action back to here.

        return: N/A
        """
        self.close()

    @Slot()
    def build_new(self):
        """
        React to the New action.

        :return: N/A
        """
        # Logic for checking we need to save and save if needed, goes here...
        # if build.needs_saving:
        #     if yes_no_dialog(self.app.tr("Save build"), self.app.tr("build name goes here"))
        if self.build.json_build is not None:
            if not self.build.ask_for_save_if_modified():
                return
        self.build_loader("Default")

    @Slot()
    def build_open(self):
        """
        React to the Open action and prompt the user to open a build.

        :return: N/A
        """
        dlg = BrowseFileDlg(self.settings, self.build, "Open", self)
        if dlg.exec():
            # Logic for checking we need to save and save if needed, goes here...
            # if build.needs_saving:
            #    if yes_no_dialog(self.app.tr("Save build"), self.app.tr("build name goes here")):
            #       self.save()
            if dlg.selected_file != "":
                self.build_loader(dlg.selected_file)

    # Open a previous build as shown on the Build Menu
    @Slot()
    def _open_previous_build(self, checked, full_path):
        """
        React to a previous build being selected from the "Build" menu.

        :param checked: Boolean: a value for if it's checked or not, always False
        :param full_path: String: Fullpath name of the build to load
        :return: N/A
        """
        # Or does the logic for checking we need to save and save if needed, go here ???
        # if self.build.needs_saving:
        # if ui_utils.save_yes_no(self.app.tr("Save build"), self.app.tr("build name goes here"))

        # open the file using the filename in the build.
        self.build_loader(full_path)

    def build_loader(self, filename_or_dict=Union[dict, str, Path], imported_name=""):
        """
        Common actions for UI components when we are loading a build.

        :param filename_or_dict: dict: the dict of an imported build (called open_import_dialog)
        :param filename_or_dict: String: the filename of file to be loaded, or "Default" if called from the New action.
        :param filename_or_dict: Path: the filename of file to be loaded, or "Default" if called from the New action.
        :param imported_name: str: The name of the build from the import dialog
        :return: N/A
        """
        # print(f"build_loader: {filename_or_dict}, {imported_name=}")
        self.alerting = False
        self.player.clear()
        self.config_ui.initial_startup_setup()
        new = filename_or_dict == "Default"
        self.settings.open_build = ""
        self.build.filename = ""
        self.build.name = "Default"
        if new:
            self.build.new(None)
        elif type(filename_or_dict) is dict:
            self.build.new(filename_or_dict)
            self.build.name = imported_name
        else:
            name, file_extension = os.path.splitext(filename_or_dict)
            path, name = os.path.split(name)
            xml = file_extension == ".xml"
            if xml:
                self.build.new(load_from_xml(filename_or_dict))
                self.build.filename = filename_or_dict.replace(".xml", ".json")
                self.build.name = name
            else:
                # open the file and update names if the file was present
                if self.build.load_from_file(filename_or_dict):
                    self.settings.open_build = filename_or_dict
                    self.build.filename = filename_or_dict
                    self.add_recent_build_menu_item()
                    self.build.name = name

        # if everything worked, lets update the UI
        if self.build.json_PoB is not None:
            # Config_UI needs to be set before the tree, as the change_tree function uses/sets it also.
            self.config_ui.load(self.build.json_config)
            # Items contain Jewels, the Tree needs Jewels, so load Items before Tree
            self.items_ui.load_from_json(self.build.json_items)
            self.tree_ui.load(self.build.json_tree, self.build.json_tree_view)
            # Skills want to know about Items and Nodes that Grant/Trigger skills, so load Skills after Items and Tree.
            self.skills_ui.load_from_json(self.build.json_skills)
            self.notes_ui.load(self.build.json_notes, self.build.json_notes_html)
            # Set UI elements that depend on the above.
            self.spin_level.setValue(self.build.level)
            self.combo_classes.setCurrentText(self.build.className)
            self.combo_ascendancy.setCurrentText(self.build.ascendClassName)
            self.player.load(self.build.json_build)

            self.set_current_tab()

        self.cb_level_auto_manual.setChecked(self.build.json_tree_view.get("level_auto_manual", False))
        # This is needed to make the jewels show. Without it, you need to select or deselect a node.
        self.gview_Tree.switch_tree(True)

        # Make sure the Main and Alt weapons are active and shown as appropriate
        self.items_ui.weapon_swap2(self.btn_WeaponSwap.isChecked())
        self.update_status_bar(f"Loaded: {self.build.name}", 10)

        self.alerting = True

        # Do calcs. Needs to be nearly last in this function
        # self.do_calcs()
        self.build.save()
        # save_to_xml("test.xml", self.build.json)

    @Slot()
    def build_save(self):
        """
        Actions required to get a filename to save a build to. Should call build_save() if user doesn't cancel.

        return: N/A
        """
        # version = self.build.version
        if self.build.filename == "":
            self.build_save_as()  # this will then call build_save()
        else:
            print(f"Saving to file: {self.build.filename}")
            name, file_extension = os.path.splitext(self.build.filename)
            xml = file_extension == ".xml"
            self.build.json_notes, self.build.json_notes_html = self.notes_ui.save()
            self.player.save()
            self.skills_ui.save_to_json()
            self.items_ui.save()
            self.config_ui.save()
            self.tree_ui.save()
            if xml:
                save_to_xml(self.build.filename, self.build.json)
            else:
                # write the file
                self.build.save_to_json()

    @Slot()
    def build_save_as(self):
        """
        Actions required to get a filename to save a build to. Should call build_save() if user doesn't cancel.

        return: N/A
        """
        # print(f"build_save_as: {self.account_name=}, {self.import_character_name=}")
        dlg = BrowseFileDlg(self.settings, self.build, "Save", self)
        if dlg.save_as_text == "" and self.import_character_name != "":
            if self.account_name:
                dlg.save_as_text = f"{self.import_character_name}, {self.import_league} league, Imported from {self.account_name}"
            else:
                dlg.save_as_text = f"{self.import_character_name} imported from {self.import_league} league"

        if dlg.exec():
            # Selected file has been checked for existing and ok'd if it does
            filename = dlg.selected_file
            print("build_save_as, file_chosen", filename)
            if filename != "":
                self.build.version = dlg.radioBtn_v2.isChecked() and 2 or 1
                self.build.filename = filename
                self.build_save()
                self.add_recent_build_menu_item()
                self.settings.open_build = self.build.version == 2 and self.build.filename or ""

    @Slot()
    def combo_item_manage_tree_changed(self, tree_label):
        """
        This is the Manage Tree combo on the Items Tab. Tell the Manage Tree combo on the Tree tab to change trees.
        :param tree_label: the name of the item just selected
        :return:
        """
        # "" will occur during a combobox clear
        if not tree_label:
            return
        # print("combo_item_manage_tree_changed", tree_label)
        self.tree_ui.combo_manage_tree.setCurrentText(tree_label)

    @Slot()
    def change_tree(self, tree_label):
        """
        Actions required when either combo_manage_tree widget changes (Tree_UI and Items_UI).
        This is here (instead of TreeUI) as the correct owner of Tree_UI and Items_UI is this class.

        :param tree_label: the name of the item just selected
                "" will occur during a combobox clear
        :return: N/A
        """
        # print("change_tree", tree_label)
        # "" will occur during a combobox clear.
        if not tree_label:
            return

        self.combo_ItemsManageTree.setCurrentText(tree_label)

        full_clear = self.build.change_tree(self.tree_ui.combo_manage_tree.currentData())

        # update label_points
        self.display_number_node_points(-1)

        # stop the tree from being updated mulitple times during the class / ascendancy combo changes
        # Also stops updating build.current_spec
        self.refresh_tree = False

        # Do Not alert about changing asscendencies when changing trees
        curr_alerting = self.alerting
        self.alerting = False
        _current_class = self.combo_classes.currentData()
        if self.build.current_spec.classId == _current_class:
            # update the ascendancy combo in case it's different
            self.combo_ascendancy.setCurrentIndex(self.build.current_spec.ascendClassId)
        else:
            # Protect the ascendancy value as it will get clobbered ...
            _ascendClassId = self.build.current_spec.ascendClassId
            # .. when this refreshes the Ascendancy combo box ...
            self.combo_classes.setCurrentIndex(self.build.current_spec.classId.value)
            # ... so we need to reset it's index
            self.combo_ascendancy.setCurrentIndex(_ascendClassId)

        set_combo_index_by_data(self.combo_Bandits, self.build.bandit)
        self.alerting = curr_alerting

        self.refresh_tree = True
        self.gview_Tree.add_tree_images(full_clear)
        self.items_ui.fill_jewel_slot_uis()
        self.show_skillset()
        self.do_calcs()

    @Slot()
    def class_changed(self, selected_class):
        """
        Slot for the Classes combobox. Triggers the curr_class property actions.

        :param selected_class: String of the selected text.
        :return:
        """
        new_class = self.combo_classes.currentData()
        # print(f"class_changed: {selected_class=}, {self.build.current_spec.classId=}, {new_class=}, {self.refresh_tree=}")
        if self.build.current_spec.classId == new_class and self.refresh_tree:
            return
        if self.alerting:
            node_num = self.build.ascendClassName == "None" and 1 or 2
            if len(self.build.current_spec.nodes) > node_num and not yes_no_dialog(
                self,
                self.tr("Resetting your Tree"),
                self.tr("Are you sure? It could be dangerous."),
            ):
                # Undo the class change
                self.combo_classes.setCurrentIndex(self.build.current_spec.classId)
                return

        # GUI Changes
        # Changing the ascendancy combobox, will trigger it's signal/slot.
        # This is good as it will set the ascendancy back to 'None'
        self.combo_ascendancy.clear()
        self.combo_ascendancy.addItem("None", 0)
        class_json = self.build.current_tree.classes[new_class.value]
        for idx, _ascendancy in enumerate(class_json["ascendancies"], 1):
            self.combo_ascendancy.addItem(_ascendancy["name"], idx)

        if self.refresh_tree:
            # build changes
            self.build.current_spec.classId = self.combo_classes.currentData()
            self.build.current_class = self.combo_classes.currentData()
            self.build.className = selected_class
            self.build.current_class = new_class
            self.build.reset_tree()
            self.gview_Tree.add_tree_images(True)

        self.do_calcs()

    @Slot()
    def ascendancy_changed(self, selected_ascendancy):
        """
        Actions required for changing ascendancies.
        :param  selected_ascendancy: String of the selected text.
                "None" will occur when refilling the combobox or when the user chooses it.
                "" will occur during a combobox clear.
        :return:
        """
        # print(f"ascendancy_changed: '{selected_ascendancy=}'", self.build.current_spec.ascendClassId_str(), self.refresh_tree)
        if selected_ascendancy == "":
            # "" will occur during a combobox clear (changing class)
            return
        current_tree = self.build.current_tree
        current_spec = self.build.current_spec
        curr_ascendancy_name = current_spec.ascendClassId_str()
        if curr_ascendancy_name != "None":
            current_nodes = set(self.build.current_spec.nodes)
            # ascendancy start node is *NOT* in this list.
            nodes_in_ascendancy = [x for x in current_tree.ascendancyMap[curr_ascendancy_name] if x in current_nodes]
            if len(nodes_in_ascendancy) > 1 and self.alerting:
                if not yes_no_dialog(
                    self,
                    self.tr("Resetting your Ascendancy"),
                    self.tr("Are you sure? It could be dangerous. Your current ascendancy points will be removed."),
                ):
                    # Don't alert on Undoing the class change.
                    self.alerting = False
                    # Undo the class change.
                    self.combo_ascendancy.setCurrentIndex(self.build.current_spec.ascendClassId)
                    self.alerting = True
                    return
                else:
                    # We do want to reset nodes.
                    for node_id in nodes_in_ascendancy:
                        self.build.current_spec.nodes.remove(node_id)

            # Remove old start node.
            self.build.current_spec.nodes.discard(current_tree.ascendancy_start_nodes[curr_ascendancy_name])

        if selected_ascendancy != "None":
            # add new start node.
            self.build.current_spec.nodes.add(current_tree.ascendancy_start_nodes[selected_ascendancy])

        if self.refresh_tree:
            self.build.current_spec.ascendClassId = self.combo_ascendancy.currentData()
            self.build.ascendClassName = selected_ascendancy
            self.gview_Tree.add_tree_images()
        self.do_calcs()

    @Slot()
    def display_number_node_points(self, bandit_id):
        """
        Actions required when the combo_bandits widget changes.

        :param bandit_id: Current text string. We don't use it.
        :return: N/A
        """
        self.build.bandit = self.combo_Bandits.currentData()
        self.max_points = self.build.bandit == "None" and 123 or 121
        nodes_assigned = (
            self.build.nodes_assigned > self.max_points
            and html_colour_text("RED", f"{self.build.nodes_assigned}")
            or f"{self.build.nodes_assigned}"
        )
        ascnodes_assigned = (
            self.build.ascnodes_assigned > 8
            and html_colour_text("RED", f"{self.build.ascnodes_assigned}")
            or f"{self.build.ascnodes_assigned}"
        )
        self.label_points.setText(f" {nodes_assigned} / {self.max_points}    {ascnodes_assigned} / 8 ")
        self.estimate_player_progress()

    def estimate_player_progress(self):
        """
        Do some educated guessing of what level the build is up to.
        :return: N/A
        """
        if self.cb_level_auto_manual.isChecked():
            return
        acts = {
            1: {"level": 1, "quest": 0, "bandit_points": 0},
            2: {"level": 12, "quest": 2, "bandit_points": 0},
            3: {"level": 22, "quest": 3},
            4: {"level": 32, "quest": 5},
            5: {"level": 40, "quest": 6},
            6: {"level": 44, "quest": 8},
            7: {"level": 50, "quest": 11},
            8: {"level": 54, "quest": 14},
            9: {"level": 60, "quest": 17},
            10: {"level": 64, "quest": 19},
            11: {"level": 67, "quest": 22},
        }
        num_nodes = self.build.nodes_assigned
        _bandits = self.build.bandit == "None" and 2 or 0
        # estimate level
        level, act = 0, 0
        for act in acts.keys():
            _bandits = self.build.bandit == "None" and acts[act].get("bandit_points", 2) or 0
            level = min(max(num_nodes - acts[act].get("quest", 22) - _bandits + 1, acts[act].get("level")), 100)
            # Break loop when we get a level less than the act
            if level <= acts.get(act + 1, {"level": 100}).get("level"):
                break

        if level < 33:
            lab_suggest = ""
        elif level < 55:
            lab_suggest = "\n  Labyrinth: Normal Lab"
        elif level < 68:
            lab_suggest = "\n  Labyrinth: Cruel Lab"
        elif level < 75:
            lab_suggest = "\n  Labyrinth: Merciless Lab"
        elif level < 90:
            lab_suggest = "\n  Labyrinth: Uber Lab"
        else:
            lab_suggest = ""

        act_progress = act == 11 and "Endgame" or f"Act: {act}"
        tip = (
            f"<pre>Required Level: {level}\nEstimated Progress:\n  {act_progress}\n  Questpoints: {acts[act].get('quest')}"
            f"\n  Extra Skillpoints: {_bandits}{lab_suggest}</pre>"
        )
        self.label_points.setToolTip(html_colour_text(self.settings.qss_default_text, tip))
        self.label_level.setToolTip(html_colour_text(self.settings.qss_default_text, tip))
        self.spin_level.setToolTip(html_colour_text(self.settings.qss_default_text, tip))
        self.build.level = level  # this will update self.spin_level

    @Slot()
    def set_tab_focus(self, index):
        """
        When switching to a tab, set the focus to a control in the tab

        :param index: Which tab got selected (0 based)
        :return: N/A
        """
        # tab indexes are 0 based. Used by set_tab_focus
        tab_focus = {
            0: self.tab_main,
            1: self.list_SocketGroups,
            2: self.list_Items,
            3: self.textedit_Notes,
            4: self.tab_main,
            5: self.tab_main,
            6: self.tab_main,
        }

        # Focus a Widget
        tab_focus.get(index).setFocus()
        # update the build
        self.build.viewMode = self.tab_main.tabWhatsThis(self.tab_main.currentIndex())
        # Turn on / off actions as needed
        self.action_ManageTrees.setVisible(self.build.viewMode == "TREE")

    @Slot()
    def open_import_dialog(self):
        """
        Open the import dialog. The dialog will return with either dlg.xml being valid (from a build share import)
         or dlg.character_data being valid (from a character download from PoE).
        If neither are valid (both = None) then the user did nothing.
        dlg.character_data is a dictionary of tree and items ({"tree": passive_tree, "items":  items})
        dlg.xml is a ET.ElementTree instance of the xml downloaded

        :return: N/A
        """
        # c = read_json("c:/git/PathOfBuilding-Python/docs/test_data/Mirabel__Sentinal_char.json")
        # t = read_json("c:/git/PathOfBuilding-Python/docs/test_data/Mirabel__Sentinal_tree.json")
        # self.build.import_passive_tree_jewels_ggg_json(t, c)
        # return
        dlg = ImportDlg(self.settings, self.build, self)
        dlg.exec()
        self.account_name = ""
        self.import_character_name = ""
        self.import_league = ""
        if dlg.xml is not None:
            self.build_loader(load_from_xml(dlg.xml), "Imported")
        elif dlg.character_data is not None:
            self.account_name = dlg.lineedit_Account.text()
            self.import_character_name = dlg.character_data["character"]["name"]
            self.import_league = dlg.character_data["character"]["league"]
            self.set_current_tab("CONFIG")
            self.combo_Bandits.showPopup()
        # If neither of those two were valid, then the user closed with no actions taken

    @Slot()
    def open_export_dialog(self):
        xml_root = save_to_xml("", self.build.json)
        dlg = ExportDlg(self.settings, xml_root, self)
        dlg.exec()

    def set_current_tab(self, tab_name: str = "") -> None:
        """
        Actions required when setting the current tab from the configuration xml file

        :param tab_name: String;  name of a tab to switch to programatically. Doesn't set the build xml if used
        :return: N/A
        """
        if tab_name == "":
            tab_name = self.build.viewMode
        for i in range(self.tab_main.count()):
            if self.tab_main.tabWhatsThis(i) == tab_name:
                self.tab_main.setCurrentIndex(i)
                return
        # If not found, set the first
        self.tab_main.setCurrentIndex(0)

    @Slot()
    def active_skill_changed(self, _skill_text: str) -> None:
        """
        Actions when changing combo_MainSkillActive

        :return: N/A
        """
        self.player.current_skill = self.skills_ui.gems_by_name_or_id.get(_skill_text, None)
        self.do_calcs()

    def load_main_skill_combo(self, _list: list) -> None:
        """
        Load the left hand socket group (under "Main Skill") controls

        :param _list: list: a list of socket group names as they appear in the skills_ui() socket group listview
        :return: N/A
        """
        # print("PoB.load_main_skill_combo", len(_list))

        # clear before disconnecting.
        # This helps for "Delete All" socket groups, resetting to a new build or loading a build.
        self.combo_MainSkill.clear()

        self.combo_MainSkill.currentTextChanged.disconnect(self.main_skill_text_changed)
        self.combo_MainSkill.currentIndexChanged.disconnect(self.main_skill_index_changed)

        # backup the current index, reload combo with new values and reset to a valid current_index
        # each line is a colon separated of socket group label and gem list
        current_index = self.combo_MainSkill.currentIndex()
        for line in _list:
            _label, _gem_list = line.split("^^^")
            self.combo_MainSkill.addItem(_label, _gem_list)
            # self.combo_MainSkill.addItem(line)
        self.combo_MainSkill.view().setMinimumWidth(self.combo_MainSkill.minimumSizeHint().width())
        # In case the new list is shorter or empty
        current_index = min(max(0, current_index), len(_list))

        self.combo_MainSkill.currentTextChanged.connect(self.main_skill_text_changed)
        self.combo_MainSkill.currentIndexChanged.connect(self.main_skill_index_changed)

        if current_index >= 0:
            self.combo_MainSkill.setCurrentIndex(current_index)

    @Slot()
    def main_skill_text_changed(self, new_text: str) -> None:
        """
        Fill out combo_MainSkillActive with the current text of combo_MainSkill

        :param new_text: string: the combo's text
        :return: N/A
        """
        if self.combo_MainSkill.currentData() is None:
            return
        try:
            self.combo_MainSkillActive.currentTextChanged.disconnect(self.active_skill_changed)
        except RuntimeError:
            pass

        self.combo_MainSkillActive.clear()
        self.combo_MainSkillActive.addItems(self.combo_MainSkill.currentData().split(", "))
        self.combo_MainSkillActive.view().setMinimumWidth(self.combo_MainSkillActive.minimumSizeHint().width())

        self.combo_MainSkillActive.currentTextChanged.connect(self.active_skill_changed)
        self.combo_MainSkillActive.setCurrentIndex(0)

    @Slot()
    def main_skill_index_changed(self, new_index: int) -> None:
        """
        Actions when changing the main skill combo. Update the Skills tab.

        :param new_index: string: the combo's index. -1 during a .clear()
        :return: N/A
        """
        # print(f"main_skill_index_changed: {new_index=}")
        if new_index == -1:
            return
        # print("main_skill_index_changed.current_index ", new_index, self.combo_MainSkill.currentText())
        # must happen before call to update_socket_group_labels
        self.build.mainSocketGroup = new_index
        self.skills_ui.update_socket_group_labels()
        self.do_calcs()

    @Slot()
    def update_status_bar(self, message: str = "", timeout: int = 5, colour: str = "") -> None:
        """
        Update the status bar. Use default text if no message is supplied.
        This triggers when the message is set and when it is cleared after the time out.
        :param message: str: the message.
        :param timeout: int: time for the message to be shown, in secs
        :param colour: str: a colour code to colour the text in the tooltip (eg "RED").
        :return: N/A
        """
        # we only care for when the message clears
        if pob_debug and message == "":
            # if message == "":
            process = psutil.Process(os.getpid())
            message = f"RAM: {'{:.2f}'.format(process.memory_info().rss / 1048576)}MB used:"
        # elif "RAM" not in message and [m for m in self.last_messages if message == m] == []:
        elif "RAM" not in message and self.last_message != message:
            self.last_message = message
            if colour:
                self.last_messages.insert(0, html_colour_text(colour, message))
            else:
                self.last_messages.insert(0, message)
            if len(self.last_messages) > 5:
                self.last_messages.pop()
            self.statusbar_MainWindow.setToolTip("<br>".join(self.last_messages))
        self.statusbar_MainWindow.showMessage(message, timeout * 1000)

    @Slot()
    def do_calcs(self, test_item: None = None, test_node: None = None) -> None:
        """
        Run luaPoB and Display Calculations.
        https://www.pythonguis.com/tutorials/pyside6-qprocess-external-programs/
        Comparison items are probs not needed, as we will need to deepcopy build, make the adjustment and call
        do_calcs. This would then need a different callback (so that would be the 1st param) who would know to compare the current stats
        to these new stats.
        :param: test_item: Item() - future comparison
        :param: test_node: Node() - future comparison
        :return: N/A
        """
        # Leave this on so we can see how many times do_calcs is called in a row. Ideally only once.
        # But changing trees ran five times on tree change.
        _debug(f"do_calcs: {self.alerting=}")
        if not self.alerting or self.calc_process is not None:
            # Don't keep calculating as a build is loaded or a thread running
            return

        self.config_ui.save()
        save_to_xml(f"{self.settings._exe_dir}/lua/src/Builds/stats.xml", self.build.json, True)

        # self.thread_data = []
        # self.calc_process = threading.Thread(target=self.do_calcs_thread(self.thread_data), daemon=True, name="PyPoB Do Calcs")
        self.calc_process = QProcess()
        _debug(f"pre_start: {self.alerting=}")
        self.calc_process.finished.connect(self.do_calcs_callback)
        self.calc_process.setWorkingDirectory(f"{self.settings._exe_dir}/lua/src")
        self.calc_process.start(f"{self.settings._exe_dir}/lua/runtime/luajit.exe", ["../PoB_jit.lua"])

    @Slot()
    def do_calcs_callback(self) -> None:
        """Callback function from luajit Process started by do_calcs"""

        def get_resist_overcap_value(res_type):
            """
            Get a resists over cap value andreturn it if it's not 0
            :param res_type: str: Fire|Cold|Lightning
            :return: str: formate string for adding to the main Res value
            """
            _value = self.player.stats.get(f"{res_type}ResistOverCap", 0)
            if _value > 0:
                _value_str = format_number(_value, " (%d%%)", self.settings)
                return html_colour_text("DARKGRAY", _value_str)
            else:
                return ""

        _debug(f"do_calcs_callback:")
        self.current_stats = bytes(self.calc_process.readAllStandardOutput()).decode("utf8").splitlines()

        # Add the lines with ' = ' in them to player Stats
        self.player.clear()
        for line in [line for line in self.current_stats if "=" in line]:
            key, value = line.strip().split(" = ")
            if value and is_str_a_number(value):
                if "." in value:
                    self.player.stats[key] = float(value)
                else:
                    self.player.stats[key] = int(value)
            elif value and value[1:].lower() in ("t", "f"):
                self.player.conditions[key] = str_to_bool(value)
            if "Minion." in key:
                # self.minion.stats[key.replace('Minion.','')] = value
                pass
            elif "MainHand." in key:
                self.player.mainhand[key.replace("MainHand.", "")] = value
            elif "OffHand." in key:
                self.player.offhand[key.replace("OffHand.", "")] = value
        # print(self.player.stats)

        # Now show them
        # print(f"{self.player.current_skill=}")
        self.textedit_Statistics.clear()
        just_added_blank = False  # Prevent duplicate blank lines. Faster than investigating the last line added of a QLineEdit.
        for stat_name in player_stats_list:
            if stat_name in ("Speed", "HitChance"):
                # ToDo: What are the other entries for ??
                # Speed has attack, spell and "". How do we differentiate?
                stat = deepcopy(player_stats_list[stat_name]["attack"])
            elif stat_name in ("ImpaleDPS", "WithImpaleDPS"):
                stat = deepcopy(player_stats_list[stat_name]["showAverage"])
            else:
                stat = deepcopy(player_stats_list[stat_name])
            # print(f"{stat_name=}, {type(stat)=}, {stat.values()=}")
            if "blank" in stat_name:
                if not just_added_blank:
                    self.textedit_Statistics.append("")
                    just_added_blank = True
            # elif stat.get("label", 0) == 0:
            # ToDo: Need to use the flag attribute to separate
            # stat = list(stat.values())[0]
            else:
                # Do we have this stat in our stats dict
                stat_value = self.player.stats.get(stat_name, bad_text)
                # print(f"{stat_name=}, {stat_value=}, {stat.get('condition', bad_text)=}")
                if stat_value != bad_text:
                    # Work out if we can show this stat
                    stat_condition = stat.get("condition", bad_text)
                    if stat_condition != bad_text:
                        if stat_condition == "Y":
                            display, stat = self.player.stat_conditions(
                                stat_name, stat_value, stat, self.player.current_skill.get("baseFlags", [])
                            )
                        else:
                            display = self.player.conditions.get(stat.get("condition"), False)
                    else:
                        display = not stat.get("hideStat", False) and stat_value != 0
                    if stat_name == "LightningMaximumHitTaken" and not display:
                        # Special Case for (Lightning,Fire,Cold)MaximumHitTaken are all the same
                        display = (
                            self.player.stats.get("LightningMaximumHitTaken", bad_text)
                            == self.player.stats.get("FireMaximumHitTaken", bad_text)
                            == self.player.stats.get("ColdMaximumHitTaken", bad_text)
                        )
                        stat["label"] = "Elemental Max Hit"

                    if display:
                        _colour = stat.get("colour", self.settings.qss_default_text)
                        _fmt = stat.get("fmt", "%d")
                        _str_value = format_number(stat_value, _fmt, self.settings, True)
                        match stat_name:
                            case "FireResist" | "ColdResist" | "LightningResist":
                                _extra_value = get_resist_overcap_value(stat_name.replace("Resist", ""))
                            case _:
                                _extra_value = ""
                        self.textedit_Statistics.append(
                            f'<span style="white-space: pre; color:{_colour};">{stat["label"]:>24}:</span> {_str_value} {_extra_value}'
                        )
                        just_added_blank = False
            self.calcs_active = False
            self.calc_process = None
            self.calcs_active = False

    @Slot()
    def do_calcs_difference_callback(self) -> None:
        """Future Callback function from luajit Process started by do_calcs to show differences"""
        pass

    @Slot()
    def do_calcs_v1(self, test_item=None, test_node=None) -> None:
        """
        Do and Display Calculations
        :param: test_item: Item() - future comparison
        :param: test_node: Node() - future comparison
        :return: N/A
        """

        def get_resist_overcap_value(res_type):
            """
            Get a resists over cap value andreturn it if it's not 0
            :param res_type: str: Fire|Cold|Lightning
            :return: str: formate string for adding to the main Res value
            """
            _value = self.player.stats.get(f"{res_type}ResistOverCap", 0)
            if _value > 0:
                _value_str = format_number(_value, " (%d%%)", self.settings)
                return html_colour_text("DARKGRAY", _value_str)
            else:
                return ""

        if not self.alerting:
            # Don't keep calculating as a build is loaded
            return
        self.config_ui.save()
        self.player.calc_stats(self.items_ui.itemset_list_active_items())
        self.textedit_Statistics.clear()
        just_added_blank = False  # Prevent duplicate blank lines. Faster than investigating the last line added of a QLineEdit.
        for stat_name in player_stats_list:
            stat = player_stats_list[stat_name]
            # print(f"{stat_name=}, {type(stat)=}, {stat.values()=}")
            if "blank" in stat_name:
                if not just_added_blank:
                    self.textedit_Statistics.append("")
                    just_added_blank = True
            elif stat.get("label", 0) == 0:
                # ToDo: Need to use the flag attribute to separate
                stat = list(stat.values())[0]
            else:
                # Do we have this stat in our stats dict
                stat_value = self.player.stats.get(stat_name, bad_text)
                if stat_value != bad_text and self.player.stat_conditions(stat_name, stat_value):
                    _colour = stat.get("colour", self.settings.qss_default_text)
                    _fmt = stat.get("fmt", "%d")
                    _str_value = format_number(stat_value, _fmt, self.settings, True)
                    match stat_name:
                        case "FireResist" | "ColdResist" | "LightningResist":
                            _extra_value = get_resist_overcap_value(stat_name.replace("Resist", ""))
                        case _:
                            _extra_value = ""
                    self.textedit_Statistics.append(
                        f'<span style="white-space: pre; color:{_colour};">{stat["label"]:>24}:</span> {_str_value} {_extra_value}'
                    )
                    just_added_blank = False

    @Slot()
    def check_clipboard_contents(self):
        """React to the O/S clipboard changing. If it's another PoB or in game copy, erase internal clipboards"""
        # print(f"QClipboard.dataChanged:  {self.clipboard.text()}")
        text = self.clipboard.text()
        # Don't react to anything that doesn't look like we want it to.
        if "Rarity:" in text or "Slot:" in text:
            self.skills_ui.internal_clipboard = []
            self.items_ui.internal_clipboard = []

    def add_item_or_node_with_skills(self, _skillset=None):
        """
        Add a skill from an equipped Item or assigned Node. Only called from ItemSlotUI(), TreeView() and Items_UI new_skill_set.
        :param _skillset: dict: Used by new_skill_set.
        :return: N/A
        """
        # print(f"equip_item_or_node_with_skills: {self.items_ui.active_hidden_skills=}, {self.build.current_spec.active_hidden_skills=}")
        for source_text, source in self.items_ui.active_hidden_skills.items() | self.build.current_spec.active_hidden_skills.items():
            # print(f"{source_text=}, {source=}")
            skill_name, level = source
            # print(skill_name, level)
            if skill_name == "":
                continue
            skill = self.skills_ui.hidden_skills_by_name_or_id.get(skill_name, {})
            if skill == {}:
                continue
            skill_set = _skillset is None and self.skills_ui.current_skill_set or _skillset
            found = [sg for sg in skill_set["SGroups"] if sg.get("source", "") == source_text]
            # print(f"2. {skill=}")
            if not found:  # no duplicates
                # add gem
                new_gem = deepcopy(empty_gem_dict)
                new_gem["nameSpec"] = skill["name"]
                new_gem["variantId"] = skill["variantId"]
                new_gem["level"] = level
                if skill.get("minionList", None):
                    new_gem["skillMinion"] = skill["minionList"][0]
                    new_gem["skillMinionSkillCalcs"] = 1
                    new_gem["skillMinionSkill"] = 1
                    new_gem["skillMinionCalcs"] = None
                new_sg = self.skills_ui.add_socket_group()
                new_sg["source"] = source_text
                new_sg["Gems"] = [new_gem]
                self.skills_ui.update_socket_group_labels()

    def remove_item_or_node_with_skills(self, source_text):
        """
        Add a skill from an equiped Item or assigned Node.
        :param source_text: str: The text to go into the gem's source field.
        :return: N/A
        """
        found = [sg for sg in self.skills_ui.current_skill_set["SGroups"] if sg.get("source", "") == source_text]
        # print(f"remove_item_or_node_with_skills: {source_text=}, {found=}")
        for sg in found:
            self.skills_ui.remove_socket_group(sg)

    def show_skillset(self):
        """Function called by Tree_UI() and Items_UI() when changing trees and Itemsets
        Remove current socket groups provided by Items or Tree nodes"""
        if self.skills_ui.current_skill_set:
            found = [sg for sg in self.skills_ui.current_skill_set["SGroups"] if sg.get("source", "") != ""]
            # print(f"MainWindow show_skillset: : {found=}")
            for sg in found:
                self.skills_ui.remove_socket_group(sg)
            self.add_item_or_node_with_skills(self.skills_ui.current_skill_set)
            # print(f'{[sg for sg in self.skills_ui.current_skill_set["SGroups"] if sg.get("source", "") != ""]=}')
