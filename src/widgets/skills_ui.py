"""
This Class manages all the UI controls and takes ownship of the controls on the "SKILLS" tab
"""

from copy import deepcopy
from pathlib import Path
import re
from random import randint

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtWidgets import QLabel, QListWidgetItem, QSizePolicy, QSpacerItem

from PoB.constants import (
    ColourCodes,
    bad_text,
    empty_skill_dict,
    empty_skillset_dict,
    empty_socket_group_dict,
    empty_gem_dict,
    quality_id,
    slot_map,
)
from PoB.settings import Settings
from PoB.build import Build
from PoB.pob_file import read_json

# from PoB.gem import Gem
from PoB.utils import _debug, bool_to_str, html_colour_text, index_exists, print_call_stack, str_to_bool
from widgets.ui_utils import set_combo_index_by_data, set_combo_index_by_text
from dialogs.popup_dialogs import yes_no_dialog
from dialogs.skillsets_dialog import ManageSkillsDlg
from widgets.gem_ui import GemUI

from ui.PoB_Main_Window import Ui_MainWindow

DefaultGemLevel_info = {
    "normalMaximum": {
        "name": "Normal Maximum",
        "tooltip": "All gems default to their highest valid non-corrupted gem level.\n",
    },
    "corruptedMaximum": {
        "name": "Corrupted Maximum",
        "tooltip": "Normal gems default to their highest valid corrupted gem level.\n"
        "Awakened gems default to their highest valid non-corrupted gem level.",
    },
    "awakenedMaximum": {
        "name": "Awakened Maximum",
        "tooltip": "All gems default to their highest valid corrupted gem level.",
    },
    "characterLevel": {
        "name": "Match Character Level",
        "tooltip": "All gems default to their highest valid non-corrupted gem level, that your character meets the"
        " level requirement for.\nThis hides gems with a minimum level requirement above your character level,"
        " preventing them from showing up in the dropdown list.",
    },
}


class SkillsUI:
    """Functions and variables to drive the interactions on the Skills Tab."""

    def __init__(self, _settings: Settings, _build: Build, _win: Ui_MainWindow) -> None:
        """
        Skills UI
        :param _build: A pointer to the currently loaded build
        :param _settings: A pointer to the settings
        :param _win: A pointer to MainWindowUI
        """
        self.settings = _settings
        self.build = _build
        self.win = _win
        self.skills = deepcopy(empty_skill_dict)
        # list of elements for the SkillSet
        self.skillsets = self.skills["SkillSets"]

        # xml element for the currently chosen skillset
        self.current_skill_set = None
        # xml element for the currently chosen socket group (the <Skill>...<Skill> tags inside a skill set)
        self.current_socket_group = None
        # list of gems from gems.json
        self.gems_by_name_or_id = {}
        self.hidden_skills_by_name_or_id = {}
        self.base_gems, self.hidden_skills = self.load_base_gems_json()
        # tracks the state of the triggers, to stop setting triggers more than once or disconnecting when not connected
        self.triggers_connected = False
        self.internal_clipboard = None
        self.dlg = None  # Is a dialog active
        # dictionary list of active nodes and items that 'Grant' skills, for use with new_skill_set
        self.active_hidden_skills = {}

        # dictionary for holding the GemUI representions of the gems in each socket group
        # self.gem_ui_list = {}

        self.win.list_SocketGroups.set_delegate()

        tr = self.settings._app.tr
        self.win.combo_SortByDPS.addItem(tr("Full DPS"), "FullDPS")
        self.win.combo_SortByDPS.addItem(tr("Combined DPS"), "CombinedDPS")
        self.win.combo_SortByDPS.addItem(tr("Total DPS"), "TotalDPS")
        self.win.combo_SortByDPS.addItem(tr("Average Hit"), "AverageDamage")
        self.win.combo_SortByDPS.addItem(tr("DoT DPS"), "TotalDot")
        self.win.combo_SortByDPS.addItem(tr("Bleed DPS"), "BleedDPS")
        self.win.combo_SortByDPS.addItem(tr("Ignite DPS"), "IgniteDPS")
        self.win.combo_SortByDPS.addItem(tr("Poison DPS"), "TotalPoisonDPS")
        self.win.combo_ShowSupportGems.addItem(tr("All"), "ALL")
        self.win.combo_ShowSupportGems.addItem(tr("Normal"), "NORMAL")
        self.win.combo_ShowSupportGems.addItem(tr("Awakened"), "AWAKENED")
        for idx, entry in enumerate(DefaultGemLevel_info.keys()):
            info = DefaultGemLevel_info[entry]
            self.win.combo_DefaultGemLevel.addItem(tr(info.get("name")), entry)
            self.win.combo_DefaultGemLevel.setItemData(idx, html_colour_text("TANGLE", tr(info.get("tooltip"))), Qt.ToolTipRole)

        # Button triggers are right to remain connected at all times as they are user initiated.
        self.win.btn_NewSocketGroup.clicked.connect(self.new_socket_group)
        self.win.btn_DeleteSocketGroup.clicked.connect(self.delete_socket_group)
        self.win.btn_DeleteAllSocketGroups.clicked.connect(self.delete_all_socket_groups)
        self.win.btn_SkillsManage.clicked.connect(self.manage_skill_sets)

        self.socket_group_to_be_moved = None
        self.win.list_SocketGroups.model().rowsMoved.connect(self.socket_groups_rows_moved)  # , Qt.QueuedConnection)
        self.win.list_SocketGroups.model().rowsAboutToBeMoved.connect(self.socket_groups_rows_about_to_be_moved)  # , Qt.QueuedConnection
        self.skill_gem_to_be_moved = None
        self.win.list_Skills.model().rowsMoved.connect(self.skill_gem_row_moved)  # , Qt.QueuedConnection)
        self.win.list_Skills.model().rowsAboutToBeMoved.connect(self.skill_gem_row_about_to_be_moved)  # , Qt.QueuedConnection

        self.list_label = QLabel(self.win.frame_SkillsRight)
        self.list_label.setWordWrap(True)
        self.list_label.setTextFormat(Qt.RichText)
        self.list_label.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignTop)
        self.vSpacer_list_label = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Do NOT turn on skill triggers here

    # def __repr__(self) -> str:
    #     return (
    #         f"Level {self.level} {self.player_class.name}" f" {self.ascendancy.value}\n"
    #         if self.ascendancy.value is not None
    #         else "\n"
    #     )

    def setup_ui(self):
        self.list_label.setMinimumSize(QSize(0, 250))
        self.win.vlayout_SkillsRight.addWidget(self.list_label)
        self.list_label.hide()

    @property
    def activeSkillSet(self) -> int:
        return self.skills.get("activeSkillSet", 0)

    @activeSkillSet.setter
    def activeSkillSet(self, new_setting):
        self.skills["activeSkillSet"] = int(new_setting)

    @property
    def sortGemsByDPSField(self) -> str:
        return self.skills.get("sortGemsByDPSField", "CombinedDPS")

    @sortGemsByDPSField.setter
    def sortGemsByDPSField(self, new_setting):
        self.skills["sortGemsByDPSField"] = new_setting

    @property
    def sortGemsByDPS(self) -> bool:
        return self.skills.get("sortGemsByDPS", True)

    @sortGemsByDPS.setter
    def sortGemsByDPS(self, new_setting):
        self.skills["sortGemsByDPS"] = new_setting

    @property
    def defaultGemQuality(self) -> int:
        return self.skills.get("activeSkillSet", 0)

    @defaultGemQuality.setter
    def defaultGemQuality(self, new_setting):
        self.skills["defaultGemQuality"] = new_setting

    @property
    def defaultGemLevel(self) -> str:
        return self.skills.get("defaultGemLevel", "normalMaximum")

    @defaultGemLevel.setter
    def defaultGemLevel(self, new_setting):
        self.skills["defaultGemLevel"] = new_setting

    @property
    def showSupportGemTypes(self) -> str:
        return self.skills.get("showSupportGemTypes", "ALL")

    @showSupportGemTypes.setter
    def showSupportGemTypes(self, new_setting):
        self.skills["showSupportGemTypes"] = new_setting

    @property
    def showAltQualityGems(self) -> bool:
        return self.skills.get("showAltQualityGems", False)

    @showAltQualityGems.setter
    def showAltQualityGems(self, new_setting):
        self.skills["showAltQualityGems"] = new_setting

    def load_from_json(self, _skills):
        """
        Load internal structures from the build object.

        :param _skills: Reference to the xml <Skills> tag set
        :return: N/A
        """
        self.skills = _skills
        self.disconnect_skill_triggers()
        # clean up
        self.change_skill_set(-1)

        self.win.check_SortByDPS.setChecked(self.sortGemsByDPS)
        set_combo_index_by_data(self.win.combo_SortByDPS, self.sortGemsByDPSField)
        self.win.check_ShowGemQualityVariants.setChecked(self.showAltQualityGems)
        set_combo_index_by_data(self.win.combo_ShowSupportGems, self.showSupportGemTypes)
        self.win.spin_DefaultGemQuality.setValue(self.defaultGemQuality)

        set_combo_index_by_data(self.win.combo_DefaultGemLevel, self.defaultGemLevel)

        # self.win.spin_DefaultGemLevel.setValue(int(level))
        # self.win.check_MatchToLevel.setChecked(
        #     str_to_bool(self.xml_skills.get("matchGemLevelToCharacterLevel", "False"))
        # )

        self.active_hidden_skills.clear()
        self.win.combo_SkillSet.clear()
        self.skillsets = self.skills["SkillSets"]

        for idx, _set in enumerate(self.skillsets):
            # print("skills_ui.load_from_json", idx, _set["title"], _set)
            self.win.combo_SkillSet.addItem(_set["title"], idx)
        # set the SkillSet ComboBox dropdown width.
        self.win.combo_SkillSet.view().setMinimumWidth(self.win.combo_SkillSet.minimumSizeHint().width())

        self.connect_skill_triggers()
        # make sure this is loaded after the skillset's
        # self.activeSkillSet = self.xml_skills.get("activeSkillSet", len(self.skill_gems_list))

        # activate trigger to run change_skill_set
        # active_skill_set = min(self.activeSkillSet, len(self.skill_gems_list) - 1)
        self.win.combo_SkillSet.setCurrentIndex(self.activeSkillSet)

    def save_to_json(self):
        """
        Save internal structures back to the build's skills object.
        The gems have been saving themselves to the xml object whenever there was a change,
          so we only need to get the other UI widget's values
        :return : xml.etree.ElementTree
        """
        self.save_socket_group_settings(None)
        self.sortGemsByDPS = self.win.check_SortByDPS.isChecked()
        self.showAltQualityGems = self.win.check_ShowGemQualityVariants.isChecked()
        self.sortGemsByDPSField = self.win.combo_SortByDPS.currentData()
        self.showSupportGemTypes = self.win.combo_ShowSupportGems.currentData()
        self.defaultGemLevel = self.win.combo_DefaultGemLevel.currentData()
        self.defaultGemQuality = self.win.spin_DefaultGemQuality.value()
        self.activeSkillSet = self.win.combo_SkillSet.currentIndex()
        # Renumber skillsets in case they have been moved, created or deleted.
        for idx, _set in enumerate(self.skills["SkillSets"]):
            _set["id"] = idx
        # print(f"skill_ui: save_to_json: {self.skills=}")
        return self.skills

    # def save_to_xml(self):
    #     """
    #     Save internal structures back to the build's skills object.
    #     The gems have been saving themselves to the xml object whenever there was a change,
    #       so we only need to get the other UI widget's values
    #     :return : xml.etree.ElementTree
    #     """
    #     xml_skills = default_skill_set_xml
    #     xml_skills.set("sortGemsByDPS", bool_to_str(self.win.check_SortByDPS.isChecked()))
    #     # xml_skills.set("matchGemLevelToCharacterLevel", bool_to_str(self.win.check_MatchToLevel.isChecked()))
    #     xml_skills.set("showAltQualityGems", bool_to_str(self.win.check_ShowGemQualityVariants.isChecked()))
    #     xml_skills.set("sortGemsByDPSField", self.win.combo_SortByDPS.currentData())
    #     xml_skills.set("showSupportGemTypes", self.win.combo_ShowSupportGems.currentData())
    #     xml_skills.set("defaultGemLevel", self.win.combo_DefaultGemLevel.currentData())
    #     xml_skills.set("defaultGemQuality", str(self.win.spin_DefaultGemQuality.value()))
    #     self.activeSkillSet = self.win.combo_SkillSet.currentIndex()
    #     # Renumber skillsets in case they have been moved, created or deleted.
    #     for idx, _set in enumerate(xml_skills.findall("SkillSet")):
    #         _set.set("id", str(idx))
    #     return xml_skills

    def load_base_gems_json(self):
        """
        Load gems.json and remove bad entries, like [Unused] and not released
        :return: dictionary of valid entries
        """

        def get_coloured_text(this_gem):
            """
            Define the coloured_text for this gem instance.

            :param this_gem: json_dict:
            :return: N/A
            """
            tags = this_gem["tags"]
            colour = ColourCodes.NORMAL.value
            if tags is not None:
                if "dexterity" in tags:
                    colour = ColourCodes.DEXTERITY.value
                elif "strength" in tags:
                    colour = ColourCodes.STRENGTH.value
                elif "intelligence" in tags:
                    colour = ColourCodes.INTELLIGENCE.value
            return colour

        def get_coloured_int(this_gem):
            """
            Define the coloured_text for this gem instance.

            :param this_gem: json_dict:
            :return: N/A
            """
            _colour = this_gem.get("colour", 0)
            match _colour:
                case 2:
                    colour = ColourCodes.DEXTERITY.value
                case 1:
                    colour = ColourCodes.STRENGTH.value
                case 3:
                    colour = ColourCodes.INTELLIGENCE.value
                case _:
                    colour = ColourCodes.NORMAL.value
            return colour

        # read in all gems but remove all invalid/unreleased ones
        # "Afflictions" will be removed by this (no display_name), so maybe a different list for them
        gems = read_json(Path(self.settings._data_dir, "base_gems.json"))
        if gems is None:
            return None, None
        # make a list by name and skillId. Index supports using the full name (Faster Attacks Support)
        #  and the display name (Faster Attacks)
        for variantId, _gem in gems.items():
            name = _gem["grantedEffect"]["name"]
            _gem["variantId"] = variantId
            _gem["colour"] = get_coloured_text(_gem)
            _gem["coloured_text"] = html_colour_text(_gem["colour"], name)

            self.gems_by_name_or_id[variantId] = _gem  # g = "AddedChaosDamageSupport"
            self.gems_by_name_or_id[name] = _gem  # name = "Added Chaos Damage"
            self.gems_by_name_or_id[_gem["grantedEffectId"]] = _gem  # grantedEffectId = "SupportAddedChaosDamagePlus"
            # Also add supports using the full name.
            if _gem.get("support", False):
                self.gems_by_name_or_id[f"{name} Support"] = _gem  # name = "Added Chaos Damage" + " Support"

        hidden = read_json(Path(self.settings._data_dir, "hidden_skills.json"))
        for variantId, _gem in hidden.items():
            _gem["colour"] = get_coloured_int(_gem)
            _gem["coloured_text"] = html_colour_text(_gem["colour"], _gem["name"])
            self.hidden_skills_by_name_or_id[variantId] = _gem
            self.hidden_skills_by_name_or_id[_gem["name"]] = _gem

        return gems, hidden
        # load_base_gems_json

    def load_base_gems_json_v1(self):
        """
        Load gems.json and remove bad entries, like [Unused] and not released
        :return: dictionary of valid entries
        """

        def get_coloured_text(this_gem):
            """
            Define the coloured_text for this gem instance.

            :param this_gem: dict: the current gem
            :return: N/A
            """
            tags = this_gem["tags"]
            colour = ColourCodes.NORMAL.value
            if tags is not None:
                if "dexterity" in tags:
                    colour = ColourCodes.DEXTERITY.value
                elif "strength" in tags:
                    colour = ColourCodes.STRENGTH.value
                elif "intelligence" in tags:
                    colour = ColourCodes.INTELLIGENCE.value
            return colour

        # read in all gems but remove all invalid/unreleased ones
        # "Afflictions" will be removed by this (no display_name), so maybe a different list for them
        gems = read_json(Path(self.settings.data_dir, "gems.json"))
        if gems is None:
            return None
        gems_list = list(gems.keys())
        for g in gems_list:
            if "Royale" in g:
                del gems[g]
                continue
            base_item = gems[g]["base_item"]
            display_name = gems[g].get("display_name", None)
            if base_item is None and display_name is None:
                del gems[g]
                continue
            if display_name is None:
                display_name = base_item.get("display_name")
            if "DNT" in display_name:
                del gems[g]
                continue
            if base_item is not None:
                if base_item["release_state"] == "unreleased":
                    del gems[g]
                    continue
                if gems[g].get("is_support", False):
                    # remove 'Support' from the name, but keep the full name as full_name
                    _name = display_name
                    gems[g]["full_name"] = _name
                    gems[g]["display_name"] = _name.replace(" Support", "")
                    base_item["display_name"] = _name.replace(" Support", "")

        # make a list by name and skill_id. Index supports using the full name (Faster Attacks Support)
        #  and the display name (Faster Attacks)
        for g in gems.keys():
            _gem = gems[g]
            display_name = _gem.get("display_name", None)
            if display_name is None:
                display_name = _gem.get("base_item").get("display_name")
            _gem["colour"] = get_coloured_text(_gem)
            _gem["coloured_text"] = html_colour_text(_gem["colour"], display_name)
            self.gems_by_name_or_id[g] = _gem
            self.gems_by_name_or_id[display_name] = _gem
            self.gems_by_name_or_id[display_name]["skillId"] = g
            # add supports using the full name
            full_name = _gem.get("full_name", None)
            if full_name is not None:
                self.gems_by_name_or_id[full_name] = _gem
                self.gems_by_name_or_id[full_name]["skillId"] = g

        return gems
        # load_base_gems_json_v1

    def connect_skill_triggers(self):
        """re-connect triggers"""
        # print("connect_skill_triggers", self.triggers_connected)
        if self.triggers_connected:
            return  # Don't re-connect
        self.triggers_connected = True
        self.win.check_SocketGroupEnabled.stateChanged.connect(self.save_socket_group_settings)
        self.win.check_SocketGroup_FullDPS.stateChanged.connect(self.save_socket_group_settings)
        self.win.combo_SocketedIn.currentIndexChanged.connect(self.save_socket_group_settings)
        self.win.lineedit_SkillLabel.textChanged.connect(self.save_socket_group_settings)
        self.win.combo_SkillSet.currentIndexChanged.connect(self.change_skill_set)
        self.win.list_SocketGroups.currentRowChanged.connect(self.change_socket_group)

    def disconnect_skill_triggers(self):
        """disconnect skill orientated triggers when updating widgets"""
        # print("disconnect_skill_triggers", self.triggers_connected)
        # print_call_stack(idx=-4)
        if not self.triggers_connected:
            # Don't disconnect if not connected
            return
        self.triggers_connected = False
        try:
            # During shutdown at least one of these will fail and alert on the command line
            self.win.check_SocketGroupEnabled.stateChanged.disconnect(self.save_socket_group_settings)
            self.win.check_SocketGroup_FullDPS.stateChanged.disconnect(self.save_socket_group_settings)
            self.win.combo_SkillSet.currentIndexChanged.disconnect(self.change_skill_set)
            self.win.combo_SocketedIn.currentIndexChanged.disconnect(self.save_socket_group_settings)
            self.win.lineedit_SkillLabel.textChanged.disconnect(self.save_socket_group_settings)
            self.win.list_SocketGroups.currentRowChanged.disconnect(self.change_socket_group)
        except RuntimeError:
            pass

    """ ################################################### SKILL SET ################################################### """

    @Slot()
    def new_skill_set(self, itemset_name="ItemSet"):
        """Create a new Skill Set and add it to the build

        :param itemset_name: str: A potential new name for this itemset
        :return: XML: The new Itemset
        """
        self.disconnect_skill_triggers()
        new_skillset = deepcopy(empty_skillset_dict)
        new_skillset["id"] = len(self.skillsets) + 1
        new_skillset["title"] = itemset_name
        self.skillsets.append(new_skillset)
        self.win.combo_SkillSet.addItem(itemset_name, new_skillset)
        # set the SkillSet ComboBox dropdown width.
        self.win.combo_SkillSet.view().setMinimumWidth(self.win.combo_SkillSet.minimumSizeHint().width())
        self.connect_skill_triggers()
        return new_skillset

    @Slot()
    def change_skill_set(self, new_index):
        """
        This triggers when the user changes skill sets using the combobox. (self.load calls it too)
        Will also activate if user changes skill sets in the manage dialog.

        :param new_index: int: index of the current selection
                               -1 will occur during a combobox clear, or some internal calls
        :return: N/A
        """
        # print("change_skill_set", new_index)
        self.current_socket_group = None
        self.clear_socket_group_settings()
        self.win.list_SocketGroups.clear()
        if 0 <= new_index < len(self.skillsets):
            self.show_skill_set(new_index, True)

    def rename_set(self, row, new_title):
        """
        Rename a set in all locations we have it set.
        :param row: int:
        :param new_title: str:
        :return: N/A
        """
        self.skillsets[row]["title"] = new_title
        self.win.combo_SkillSet.setItemText(row, new_title)

    def show_skill_set(self, _index=0, trigger=False):
        """
        Show a set of skills.
        :param _index: int: set the current socket group active at the end of the function
        :param trigger: bool:  if True, this is called from a trigger, so don't disconnect/reconnect triggers
        :return: N/A
        """
        # print("show_skill_set", _index, self.win.combo_SkillSet.currentText(), _set)
        if not trigger:
            self.disconnect_skill_triggers()

        if 0 <= _index < len(self.skillsets):
            self.current_skill_set = self.skillsets[_index]
            # Find all Socket Groups and add them to the Socket Group list
            socket_groups = self.current_skill_set["SGroups"]

            self.win.list_SocketGroups.clear()
            for idx, group in enumerate(socket_groups):
                self.win.list_SocketGroups.addItem(self.define_socket_group_label(None, group))

            # Load the left hand socket group (under "Main Skill") widgets
            self.load_main_skill_combo()

            if not trigger:
                self.connect_skill_triggers()
            # Trigger the filling out of the right hand side UI elements using change_socket_group -> load_socket_group
            self.win.list_SocketGroups.setCurrentRow(0)
            # Use change_socket_group using mainActiveSkill -1

            self.win.add_item_or_node_with_skills(self.current_skill_set)

    def delete_skill_set(self, itemset_num):
        """
        Delete ONE skillset
        :param itemset_num: int: the item to be removed.
        """
        # print(f"delete_skill_set: {itemset_num=}, {self.skillsets=}")
        if self.current_skill_set == self.skillsets[itemset_num]:
            if len(self.skillsets) == 1:
                self.current_skill_set = None
            else:
                self.current_skill_set = self.skillsets[itemset_num == 0 and 0 or itemset_num - 1]
        self.skillsets.pop(itemset_num)
        self.win.combo_SkillSet.removeItem(itemset_num)

    def delete_all_skill_sets(self, prompt=True):
        """Delete all skill sets

        :param prompt: boolean: If called programatically from importing a build, this should be false,
                                elsewise prompt the user to be sure.
        :return: N/A
        """
        # print("delete_all_skill_sets")
        tr = self.settings._app.tr
        if not prompt or yes_no_dialog(
            self.win,
            tr("Delete all Skill Sets"),
            tr(" This action has no undo. Are you sure ?"),
        ):
            self.disconnect_skill_triggers()
            self.current_skill_set = None
            self.skillsets.clear()
            self.win.combo_SkillSet.clear()
            self.connect_skill_triggers()

    def move_set(self, start, destination):
        """
        Move a set entry. This is called by the manage sets dialog.

        :param start: int: the index of the set to be moved
        :param destination: the index where to insert the moved set
        :return:
        """
        print("skill_ui.move_set", start, destination)
        if start < destination:
            # need to decrement dest by one as we are going to remove start first
            destination -= 1
        _set = self.skillsets.pop(start)
        self.skillsets.insert(destination, _set)
        # Turn off triggers whilst moving the combobox to stop unnecessary updates)
        self.disconnect_skill_triggers()
        curr_index = self.win.combo_SkillSet.currentIndex()
        self.win.combo_SkillSet.removeItem(start)
        self.win.combo_SkillSet.insertItem(destination, _set.get("title", "Default"), _set)
        # set the SkillSet ComboBox dropdown width.
        self.win.combo_SkillSet.view().setMinimumWidth(self.win.combo_SkillSet.minimumSizeHint().width())
        if start == curr_index:
            self.win.combo_SkillSet.setCurrentIndex(destination)
        self.connect_skill_triggers()

    def copy_skill_set(self, index, new_name):
        """
        Copy a set and return the new copy
        :param index: the row the current set is on.
        :param new_name: str: the new set's name
        :return: xml.etree.ElementTree: The new set
        """
        new_skillset = deepcopy(self.skillsets[index])
        index += 1
        new_skillset["title"] = new_name
        self.skillsets.insert(index, new_skillset)
        self.disconnect_skill_triggers()
        self.win.combo_SkillSet.insertItem(index, new_name, new_skillset)
        self.connect_skill_triggers()
        return new_skillset

    def manage_skill_sets(self):
        """
        and we need a dialog ...
        :return: N/A
        """
        # Ctrl-M (from MainWindow) won't know if there is another window open, so stop opening another instance.
        if self.dlg is None:
            self.dlg = ManageSkillsDlg(self, self.settings, self.win)
            self.dlg.exec()
            self.dlg = None

    """ ################################################### SOCKET GROUP ################################################### """

    def load_main_skill_combo(self):
        """
        Load the left hand socket group (under "Main Skill") controls

        :return: N/A
        """
        self.win.load_main_skill_combo(
            # whatsThis has the un-coloured/un-altered text
            [self.win.list_SocketGroups.item(i).whatsThis() for i in range(self.win.list_SocketGroups.count())]
        )

    def define_socket_group_label(self, item=None, group=None):
        """
        Setup the passed in QListWidgetItem's text depending on whether it's active or not, etc.

        :param item: QListWidgetItem:
        :param group: ElementTree.Element:
        :return: QListWidgetItem
        """
        # print(f"define_socket_group_label: , {item=}, {group=}")
        if group is None:
            group = self.current_socket_group
        if group is None:
            return
        if item is None:
            item = QListWidgetItem("")

        # build a gem list from active skills if needed
        _gem_list = ""
        for _gem in group["Gems"]:
            # If this gem is not a support gem and is enabled (the far right widget)
            if "Support" not in _gem.get("variantId") and _gem.get("enabled"):
                _gem_list += f'{_gem.get("nameSpec")}, '

        if _gem_list == "":
            _gem_list = "-no active skills-"
        else:
            _gem_list = _gem_list.rstrip(", ")

        _label = group.get("label")
        if _label == "" or _label is None:
            _label = _gem_list

        # set enabled based on the group control and whether there is an active skill in the group
        enabled = group.get("enabled") and not (_label == "" or _label == "-no active skills-")
        full_dps = group.get("includeInFullDPS", "False")
        sg_idx = self.current_skill_set["SGroups"].index(group)
        active = self.win.combo_MainSkill.currentIndex() == sg_idx and enabled

        # get a copy of the label with out all the extra information or colours.  Was using : but content providers use it.
        item.setWhatsThis(f"{_label}^^^{_gem_list}")

        _label += (
            f"{not enabled and ' Disabled' or ''}"
            f"{full_dps and html_colour_text('TANGLE', ' (FullDPS)') or ''}"
            f"{active and html_colour_text('RELIC', ' (Active)') or ''}"
        )

        # change colour (dim) if it's disabled or no active skills
        if enabled:
            _label = html_colour_text("NORMAL", _label)
        else:
            _label = html_colour_text("LIGHTGRAY", _label)
        # print(_label)

        item.setText(_label)
        return item

    def update_socket_group_labels(self):
        """
        This changes the text on the 'active' socket group list as the main skill combo (far left) is
        changed. Called from MainWindow(), so may belong in that class.

        :return: N/A
        """
        # print("update_socket_group_labels", self.win.list_SocketGroups.count())
        if self.win.list_SocketGroups.count() == 0:
            return
        for idx in range(self.win.list_SocketGroups.count()):
            item = self.win.list_SocketGroups.item(idx)
            # print("update_socket_group_labels", idx, self.current_skill_set["SGroups"][idx])
            self.define_socket_group_label(item, self.current_skill_set["SGroups"][idx])

    @Slot()
    def delete_socket_group(self):
        """Delete a socket group"""
        # print("delete_socket_group")
        if self.current_skill_set is not None and self.current_socket_group is not None:
            self.remove_socket_group(self.current_socket_group)

    def remove_socket_group(self, _sg):
        """
        Remove a socket group
        :param _sg: dict: The group to be removed.
        :return: N/A
        """
        # print(f"remove_socket_group: {_sg}")
        try:
            curr_row = self.win.list_SocketGroups.currentRow()
            idx = _sg and self.current_skill_set["SGroups"].index(_sg) or curr_row
            self.disconnect_skill_triggers()
            self.win.list_SocketGroups.takeItem(idx)
            del self.current_skill_set["SGroups"][idx]
            if len(self.current_skill_set) == 0:
                # empty all skill/socket widgets
                self.change_skill_set(-1)
            elif idx == curr_row:
                self.connect_skill_triggers()
                # Trigger the filling out of the RHS UI elements using change_socket_group -> load_socket_group
                self.win.list_SocketGroups.setCurrentRow(min(idx, self.win.list_SocketGroups.count()))
            self.update_socket_group_labels()
            self.load_main_skill_combo()
            self.connect_skill_triggers()
        except ValueError:
            pass

    @Slot()
    def delete_all_socket_groups(self, prompt=True):
        """
        Delete all socket groups.

        :param prompt: boolean: If called programatically from importing a build, this should be false,
                                elsewise prompt the user to be sure.
        :return: N/A
        """
        # print("delete_all_socket_groups")
        if self.current_skill_set is None or len(list(self.current_skill_set)) == 0:
            return
        tr = self.settings._app.tr
        if not prompt or yes_no_dialog(
            self.win,
            tr("Delete all Socket Groups"),
            tr(" This action has no undo. Are you sure ?"),
        ):
            self.disconnect_skill_triggers()
            self.current_skill_set["SGroups"].clear()
            # empty all skill/socket widgets
            self.change_skill_set(-1)
            self.load_main_skill_combo()
            self.connect_skill_triggers()

    @Slot()
    def new_socket_group(self):
        """Create a new socket group. Actions for when the new socket group button is pressed."""
        # print("new_socket_group")
        self.add_socket_group()
        # Trigger the filling out of the right hand side UI elements using change_socket_group -> load_socket_group
        idx = len(self.current_skill_set) - 1
        self.win.list_SocketGroups.setCurrentRow(idx)

    def add_socket_group(self):
        """
        Create a new socket group.
        return: Socket Group: dict:
        """
        new_socket_group = deepcopy(empty_socket_group_dict)
        if self.current_skill_set is None:
            self.current_skill_set = self.new_skill_set()
        self.current_skill_set["SGroups"].append(new_socket_group)
        self.win.list_SocketGroups.addItem(self.define_socket_group_label(group=new_socket_group))
        self.update_socket_group_labels()
        return new_socket_group

    def clear_socket_group_settings(self):
        """
        Clear all the widgets on the top right of the Skills tab.

        :return: N/A
        """
        self.disconnect_skill_triggers()
        self.clear_gem_ui_list()
        self.win.combo_SocketedIn.setCurrentIndex(-1)
        self.win.lineedit_SkillLabel.setText("")
        self.win.check_SocketGroupEnabled.setChecked(False)
        self.win.check_SocketGroup_FullDPS.setChecked(False)
        self.connect_skill_triggers()

    @Slot()
    def change_socket_group(self, _new_group):
        """
        This triggers when the user changes an entry on the list of skills.

        :param _new_group: int: row number.
               -1 will occur during a combobox clear
        :return: N/A
        """
        # print("change_socket_group", _new_group)
        # Clean up and save objects. If _index = -1, then this is the only thing emptying these widgets
        # these routines have the connect and disconnect routines
        if index_exists(self.current_skill_set["SGroups"], _new_group):
            self.clear_socket_group_settings()
            self.load_socket_group(_new_group)

    def check_socket_group_for_an_active_gem(self, _sg):
        """
        Check a socket group and if the first gem is not an active gem, find an active gem in the group
        and if found, set it to be first.

        :param _sg: dict: the socket group to check
        :return: N/A
        """
        if _sg is not None:
            gem_list = _sg.get("Gems", [])
            for _idx, _gem in enumerate(gem_list):
                # find the first active gem and move it if it's index is not 0
                if "Support" not in _gem.get("skillId"):
                    if _idx != 0:
                        gem_list.remove(_gem)
                        gem_list.insert(0, _gem)
                    break

    def load_socket_group(self, _index):
        """
        Load a socket group into the UI, unloading the previous one.

        :param _index: index to display, 0 based integer
        :return: N/A
        """
        # print(f"load_socket_group: {_index=}")
        self.disconnect_skill_triggers()

        sgroups = self.current_skill_set["SGroups"]
        if index_exists(sgroups, _index):
            # assign and setup new group
            self.current_socket_group = sgroups[_index]
            if self.current_socket_group is not None:
                self.win.vlayout_SkillsRight.removeItem(self.vSpacer_list_label)
                self.build.check_socket_group_for_an_active_gem(self.current_socket_group)
                self.win.lineedit_SkillLabel.setText(self.current_socket_group.get("label"))
                set_combo_index_by_text(self.win.combo_SocketedIn, self.current_socket_group.get("slot"))
                self.win.check_SocketGroupEnabled.setChecked(self.current_socket_group.get("enabled", False))
                self.win.check_SocketGroup_FullDPS.setChecked(self.current_socket_group.get("includeInFullDPS", False))
                if len(self.current_socket_group["Gems"]) > 0:
                    gem0 = self.current_socket_group["Gems"][0]
                    source = self.current_socket_group.get("source", "")
                    self.win.list_Skills.setHidden(source != "")
                    self.list_label.setHidden(source == "")
                    if gem0 and source:
                        # Gem provided by an item or tree
                        t = re.search(r"Tree:(\d+)$", source)
                        i = re.search(r"Item:(\d+):(.*)$", source)
                        hskill = self.hidden_skills[gem0["variantId"]]
                        if t:
                            if int(t.group(1)) in self.build.current_spec.nodes:
                                tree_node = self.build.current_tree.nodes.get(int(t.group(1)), None)
                                if tree_node:
                                    label = (
                                        f"This is a special group created for the {hskill['coloured_text']} skill, which is being provided by "
                                        f"{tree_node.name}.<br>You cannot delete this group, but it will disappear if you un-allocate the node."
                                    )
                                    # print(label)
                                    self.list_label.setText(label)
                                    self.win.vlayout_SkillsRight.addItem(self.vSpacer_list_label)
                            else:
                                # Remove this SG, Node no longer allocated.
                                self.win.remove_item_or_node_with_skills(source)
                        elif i:
                            _item = self.win.items_ui.itemlist_by_id.get(int(i.group(1)), 0)
                            if _item:
                                label = (
                                    f"This is a special group created for the {hskill['coloured_text']} skill, which is being provided by "
                                    f"{_item.coloured_text}. You cannot delete this group, but it will disappear if you un-equip "
                                    f"the item.<br><br>You cannot add support gems to this group, but support gems in any other group "
                                    f"socketed into {_item.coloured_text} will automatically apply to the skill."
                                )
                                self.list_label.setText(label)
                                self.win.vlayout_SkillsRight.addItem(self.vSpacer_list_label)
                            else:
                                # Remove this SG, Item no longer equipped
                                self.win.remove_item_or_node_with_skills(source)
                    else:
                        # No "Source", so regular Socket Group
                        for idx, gem in enumerate(self.current_socket_group["Gems"]):
                            self.create_gem_ui(idx, gem)
                        # Create an empty gem at the end
                        self.create_gem_ui(len(self.current_socket_group["Gems"]), None)
                else:
                    # Create an empty gem at the end
                    self.list_label.setHidden(True)
                    self.win.list_Skills.setHidden(False)
                    self.create_gem_ui(len(self.current_socket_group["Gems"]), None)

        self.connect_skill_triggers()

    @Slot()
    def save_socket_group_settings(self, info):
        """
        Actions for when the socket group settings are altered. Save to xml. Do *NOT* call internally.

        :param info: Some sort of info for a widget. EG: checked state for a checkBox, text for a comboBox.
        :return: N/A
        """
        if self.current_socket_group is not None:
            # print(f"save_socket_group_settings, {type(info)}, '{info}'")
            self.current_socket_group["slot"] = self.win.combo_SocketedIn.currentText()
            self.current_socket_group["label"] = self.win.lineedit_SkillLabel.text()
            self.current_socket_group["enabled"] = self.win.check_SocketGroupEnabled.isChecked()
            self.current_socket_group["includeInFullDPS"] = self.win.check_SocketGroup_FullDPS.isChecked()
            item = self.win.list_SocketGroups.currentItem()
            # stop a recursion error as save_socket_group_settings is called from define_socket_group_label as well
            if info is not None:
                self.define_socket_group_label(item)
            self.load_main_skill_combo()

    @Slot()
    def socket_groups_rows_moved(self, parent, start, end, destination, dest_row):
        """
        Respond to a socket group being moved, by moving it's matching dict. It's called 4 times (sometimes)

        :param parent: QModelIndex: not Used.
        :param start: int: where the row was moved from.
        :param end: int: not Used. It's the same as start as multi-selection is not allowed.
        :param destination: QModelIndex: not Used.
        :param dest_row: int: The destination row.
        :return: N/A
        """
        print("socket_groups_rows_moved")
        # if not None, do move in current_socket_group and set self.socket_group_to_be_moved = None
        # this way the last three are ignored.
        if self.socket_group_to_be_moved is None:
            return
        # Do move
        if self.current_skill_set is not None:
            if start < dest_row:
                # need to decrement dest by one as we are going to remove start first
                dest_row -= 1
            _sg = self.current_skill_set.pop(start)
            self.current_skill_set.insert(dest_row, _sg)

        # reset to none, this way we only respond to the first call of the four.
        self.socket_group_to_be_moved = None

    @Slot()
    def socket_groups_rows_about_to_be_moved(self, source_parent, source_start, source_end, dest_parent, dest_row):
        """
        Setup for a socket group move. It's called 4 times (sometimes).

        :param source_parent: QModelIndex: Used to notify the move
        :param source_start: int: not Used
        :param source_end: int: not Used
        :param dest_parent: QModelIndex: not Used
        :param dest_row: int: not Used
        :return: N/A
        """
        # print("socket_groups_rows_about_to_be_moved")
        self.socket_group_to_be_moved = source_parent

    def get_item_from_clipboard(self, data=None):
        """

        :param data: str: the clipboard data or None. Sanity checked to be an Item Class of Gem
        :return: bool: success
        """
        """Get an item from the windows or internal clipboard"""
        print("SkillsUI.get_item_from_clipboard: Ctrl-V pressed")
        if self.internal_clipboard is None:
            print("real clipboard")
        else:
            print("Internal clipboard")
            self.internal_clipboard = None
        return False

    """ ################################################### GEM UI ################################################### """

    def gem_ui_notify(self, w_item: QListWidgetItem):
        """
        React to a wigdet change from an instance of GemUI(), where that widget is not the remove button.

        :param w_item: the triggering WidgetItem from list_Skills.
        :return: N/A
        """
        row = self.win.list_Skills.row(w_item)
        gem_ui: GemUI = self.win.list_Skills.itemWidget(w_item)
        # print(f"gem_ui_notify1:, {w_item.text()=}, {row=}, {gem_ui=}")
        # If gem_ui.gem *is* in self.current_socket_group["Gems"], then we are altering an existing gemUI, and don't add it.
        if gem_ui.gem is not None and gem_ui.variantId != "" and gem_ui.gem not in self.current_socket_group["Gems"]:
            self.current_socket_group["Gems"].append(gem_ui.gem)
            # print(f"gem_ui_notify2: {gem_ui.variantId} not found, adding.")
            # Create an empty gem at the end
            self.create_gem_ui(len(self.current_socket_group["Gems"]), None)
        self.update_socket_group_labels()
        self.load_main_skill_combo()

    def create_gem_ui(self, index, gem=None):
        """
        Add a new row to the Skills list.

        :param index: int: number of this gem in this skill group
        :param gem: dict: The item to be added (from the build json)
        :return:
        """
        # print("create_gem_ui", index, gem)
        item = QListWidgetItem()
        self.win.list_Skills.insertItem(index, item)
        gem_ui = GemUI(item, self.gems_by_name_or_id, self.gem_ui_notify, self.settings, gem)
        gem_ui.fill_gem_list(self.base_gems, self.win.combo_ShowSupportGems.currentText())
        item.setSizeHint(gem_ui.sizeHint())
        self.win.list_Skills.setItemWidget(item, gem_ui)

        # this is for deleting the gem
        gem_ui.btn_GemRemove.clicked.connect(lambda checked: self.gems_remove_checkbox_selected(item, gem_ui))
        return gem_ui

    def clear_gem_ui_list(self):
        """
        Clear the gem_ui_list, destroying the UI elements as we go.

        :return: N/A
        """
        # print(f"clear_gem_ui_list, self.win.list_Skills.count()={self.win.list_Skills.count()}")
        for idx, w_item in enumerate(self.win.list_Skills.items(None)):
            gem_ui = self.win.list_Skills.itemWidget(w_item)
            # print("clear_gem_ui_list", idx)
            if gem_ui is not None and gem_ui.gem is not None:
                # Don't notify, cause that causes a loop
                gem_ui.save(False)
        self.win.list_Skills.clear()

    def remove_gem_ui(self, index):
        """
        Remove a GemUI class. TBA on full actions needed. May not be needed

        :param index: int: index of frame/GemUI() to remove
        :return:
        """
        print("remove_gem_ui")
        if index_exists(self.gem_ui_list, index):
            self.current_socket_group["Gems"].remove(index)
            # self.current_skill_set[_index].remove(self.gem_ui_list[index].gem)
            del self.gem_ui_list[index]
        # update all gem_ui's index in case the one being deleted was in the middle
        for idx, key in enumerate(self.gem_ui_list.keys()):
            self.gem_ui_list[key].index = idx

    @Slot()
    def gems_remove_checkbox_selected(self, item, gem_ui):
        """
        Actions required for selecting the red cross to the left of the GemUI().

        :param item: the row passed through to/from lambda
        :param gem_ui: the GemUI passed through to/from lambda
        :return: N/A
        """
        print("gems_remove_checkbox_selected", item, gem_ui)
        row = self.win.list_Skills.row(item)
        self.win.list_Skills.takeItem(row)
        _gem = gem_ui.gem
        if self.current_socket_group is not None and _gem in self.current_socket_group["Gems"]:
            # print("gem_ui_notify", row, ui)
            # self.remove_gem_ui(_key)
            self.current_socket_group["Gems"].remove(_gem)
        # Make sure there is always one GemUI available
        if self.win.list_Skills.count() == 0:
            self.create_gem_ui(0)
        self.update_socket_group_labels()
        self.load_main_skill_combo()

    def skill_gem_row_moved(self, parent, start, end, destination, dest_row):
        """
        Respond to a socket group being moved, by moving it's matching xml element. It's called 4 times (sometimes)

        :param parent: QModelIndex: not Used.
        :param start: int: where the row was moved from.
        :param end: int: not Used. It's the same as start as multi-selection is not allowed.
        :param destination: QModelIndex: not Used.
        :param dest_row: int: The destination row.
        :return: N/A
        """
        # print("skill_gem_row_moved")
        # if not None, do move in current_xml_group and set self.socket_group_to_be_moved = None
        # this way the last three are ignored.
        if self.socket_group_to_be_moved is None:
            return
        # Do move
        if self.current_socket_group is not None:
            # item = self.win.list_SocketGroups.item(start)
            if start < dest_row:
                # need to decrement dest by one as we are going to remove start first
                dest_row -= 1
            _sg = self.current_socket_group.pop(start)
            self.current_socket_group.insert(dest_row, _sg)

        # reset to none, this way we only respond to the first call of the four.
        self.skill_gem_to_be_moved = None

    @Slot()
    def skill_gem_row_about_to_be_moved(self, source_parent, source_start, source_end, dest_parent, dest_row):
        """
        Setup for a socket group move. It's called 4 times (sometimes).

        :param source_parent: QModelIndex: Used to notify the move
        :param source_start: int: not Used
        :param source_end: int: not Used
        :param dest_parent: QModelIndex: not Used
        :param dest_row: int: not Used
        :return: N/A
        """
        # print("skill_gem_row_about_to_be_moved")
        self.skill_gem_to_be_moved = source_parent

    def import_gems_ggg_json(self, json_items, delete_all):
        """
        Import skills from the json supplied by GGG.

        :param json_items: json import of the item data (that contains skill gem info)
        :param delete_all: bool: True will delete everything first.
        :return: int: number of skillsets
        """

        def get_property(_json_gem, _name, _default):
            """
            Get a property from a list of property tags. Not all properties appear mandatory.

            :param _json_gem: the gem reference from the json download
            :param _name: the name of the property
            :param _default: a default value to be used if the property is not listed
            :return:
            """
            for _prop in _json_gem.get("properties"):
                if _prop.get("name") == _name:
                    value = _prop.get("values")[0][0].replace(" (Max)", "").replace("+", "").replace("%", "")
                    return value
            return _default

        # print("import_gems_ggg_json", len(json_items["items"]))
        if len(json_items["items"]) <= 0:
            return
        if delete_all:
            self.delete_all_socket_groups(False)
            self.delete_all_skill_sets(False)

        # Make a new skill set
        json_character = json_items.get("character")
        self.current_skill_set = self.new_skill_set(f"Imported {json_character.get('name', '')}")
        self.delete_all_socket_groups(False)

        # loop through all items and look for gems in socketedItems
        for item in json_items["items"]:
            if item.get("socketedItems", None) is not None:
                # setup tracking of socket group changes in one item
                current_socket_group = None
                current_socket_group_number = -1
                for idx, json_gem in enumerate(item.get("socketedItems")):
                    # let's get the group # for this socket ...
                    this_group = item["sockets"][idx]["group"]
                    # ... so we can make a new one if needed
                    if this_group != current_socket_group_number:
                        self.check_socket_group_for_an_active_gem(current_socket_group)
                        current_socket_group_number = this_group
                        current_socket_group = self.add_socket_group()
                        current_socket_group["slot"] = slot_map[item["inventoryId"]]
                    _gem = deepcopy(empty_gem_dict)
                    current_socket_group["Gems"].append(_gem)
                    _gem["level"] = int(get_property(json_gem, "Level", "1"))
                    _gem["quality"] = int(get_property(json_gem, "Quality", "0"))

                    """
                    new
                    gemId="Metadata/Items/Gems/SupportGemFeedingFrenzy" 	<-skillId
                    variantId="FeedingFrenzySupport" 						<-Dict Key also variantId
                    skillId="SupportMinionOffensiveStance" 					<-grantedEffectId
                    nameSpec="Feeding Frenzy"								<-grantedEffect.name

                    old
                    gemId="Metadata/Items/Gems/SupportGemImpendingDoom"		<-skillId
                    skillId="ViciousHexSupport"								<-Dict Key
                    nameSpec="Impending Doom"								<-grantedEffect.name
                    """
                    _name = json_gem["baseType"].replace(" Support", "")
                    _gem["nameSpec"] = _name

                    _gem["variantId"] = self.gems_by_name_or_id[_name]["variantId"]
                    _gem["skillId"] = self.gems_by_name_or_id[_name]["grantedEffectId"]

                    # _gem.set("gemId", base_item.get("id"))
                    # q = json_gem.get("typeLine", "Anomalous")
                    # _gem["qualityId"] = quality_id[q]

                self.check_socket_group_for_an_active_gem(current_socket_group)
        self.win.combo_SkillSet.setCurrentIndex(0)
        self.show_skill_set(0, True)

    def import_from_poep_json(self, json_skills, skillset_name):
        """
        Import skills from poeplanner.com json import
        :param json_skills: json: just the skills portion
        :param skillset_name: str: the name of the skill set
        :return: N/A
        """
        self.delete_all_socket_groups(False)
        self.delete_all_skill_sets(False)
        self.current_skill_set = self.new_skill_set(skillset_name)
        self.delete_all_socket_groups(False)

        for json_group in json_skills["groups"]:
            current_socket_group = self.add_socket_group()
            _slot = json_group.get("equipmentSlot", "")
            if _slot != "":
                current_socket_group["slot"] = slot_map[_slot.title()]
            for idx, json_gem in enumerate(json_group.get("skillGems")):
                _gem = deepcopy(empty_gem_dict)
                current_socket_group["Gems"].append(_gem)
                _gem["level"] = json_gem.get("level", 1)
                _gem["quality"] = json_gem.get("quality", 0)
                _gem["enabled"] = json_gem.get("enabled", False)

                """
                new
                gemId="Metadata/Items/Gems/SupportGemFeedingFrenzy" 	<-skillId
                variantId="FeedingFrenzySupport" 						<-Dict Key also variantId
                skillId="SupportMinionOffensiveStance" 					<-grantedEffectId
                nameSpec="Feeding Frenzy"								<-grantedEffect.name

                old
                gemId="Metadata/Items/Gems/SupportGemImpendingDoom"		<-skillId
                skillId="ViciousHexSupport"								<-Dict Key
                nameSpec="Impending Doom"								<-grantedEffect.name
                """
                _name = json_gem["name"].replace(" Support", "")
                _gem["nameSpec"] = _name
                _gem["variantId"] = self.gems_by_name_or_id[_name]["variantId"]
                _gem["skillId"] = self.gems_by_name_or_id[_name]["grantedEffectId"]
                # _gem.set("gemId", base_item.get("id"))

                # q = json_gem.get("typeLine", "Anomalous")
                # _gem["qualityId"] = quality_id[q]

            self.check_socket_group_for_an_active_gem(current_socket_group)
        self.win.combo_SkillSet.setCurrentIndex(0)
        self.show_skill_set(0, True)


# def test() -> None:
#     skills_ui = SkillsUI()
#     print(skills_ui)
#
#
# if __name__ == "__main__":
#     test()
