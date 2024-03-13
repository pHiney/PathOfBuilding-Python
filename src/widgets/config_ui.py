"""
This Class manages all the elements and owns some elements of the "CONFIG" tab
"""

from PySide6.QtWidgets import QGridLayout

from PoB.constants import default_max_charges
from PoB.settings import Settings
from PoB.build import Build
from widgets.ui_utils import set_combo_index_by_data, print_a_xml_element

from ui.PoB_Main_Window import Ui_MainWindow


class ConfigUI:
    def __init__(self, _settings: Settings, _build: Build, _win: Ui_MainWindow) -> None:
        """
        Config UI
        :param _build: A pointer to the currently loaded build
        :param _settings: A pointer to the settings
        :param _win: A pointer to MainWindowUI
        """
        self.settings = _settings
        self.build = _build
        self.win = _win
        self.json_config = {}

    def load(self, _config: dict):
        """
        Load UI Widgets from the build object
        :param: _config: dict. The build's copy of json_config
        """
        # print("config.load", self.build.version, self.build.className, print_a_xml_element(_config))
        self.json_config = _config
        _input = self.json_config["Input"]

        # General
        set_combo_index_by_data(self.win.combo_ResPenalty, self.build.resistancePenalty)
        set_combo_index_by_data(self.win.combo_Bandits, self.build.bandit)
        set_combo_index_by_data(self.win.combo_MajorPantheon, self.build.pantheonMajorGod)
        set_combo_index_by_data(self.win.combo_MinorPantheon, self.build.pantheonMinorGod)
        set_combo_index_by_data(self.win.combo_igniteMode, _input.get("igniteMode", "AVERAGE"))
        set_combo_index_by_data(self.win.combo_EHPUnluckyWorstOf, _input.get("EHPUnluckyWorstOf", 1))

        # Combat
        self.win.check_PowerCharges.setChecked(_input.get("usePowerCharges", False))
        self.win.spin_NumPowerCharges.setValue(_input.get("overridePowerCharges", default_max_charges))
        self.win.check_FrenzyCharges.setChecked(_input.get("useFrenzyCharges", False))
        self.win.spin_NumFrenzyCharges.setValue(_input.get("overrideFrenzyCharges", default_max_charges))
        self.win.check_EnduranceCharges.setChecked(_input.get("useEnduranceCharges", False))
        self.win.spin_NumEnduranceCharges.setValue(_input.get("overrideEnduranceCharges", default_max_charges))
        self.win.check_SiphoningCharges.setChecked(_input.get("useSiphoningCharges", False))
        self.win.spin_NumSiphoningCharges.setValue(_input.get("overrideSiphoningCharges", default_max_charges))
        self.win.check_ChallengerCharges.setChecked(_input.get("useChallengerCharges", False))
        self.win.spin_NumChallengerCharges.setValue(_input.get("overrideChallengerCharges", default_max_charges))
        self.win.check_BlitzCharges.setChecked(_input.get("useBlitzCharges", False))
        self.win.spin_NumBlitzCharges.setValue(_input.get("overrideBlitzCharges", default_max_charges))
        self.win.check_GhostCharges.setChecked(_input.get("useGhostCharges", False))
        self.win.spin_NumGhostCharges.setValue(_input.get("overrideGhostCharges", default_max_charges))
        # waitForMaxSeals

        _input.get("customMods", "default")
        custom_mods = _input.get("customMods", "")
        self.win.textedit_CustomModifiers.setPlainText(custom_mods.replace("~^", "\n"))

    def load_from_xml(self, _config):
        """
        Load internal structures from the build object
        :param _config: Reference to the xml <Config> tag set
        """
        # print("config.load_from_xml", self.build.version, self.build.className, print_a_xml_element(_config))
        _input = {}

        # A list of _config.findall("Input) and create a new dictonary from it and call self.load()
        for xml_input in _config.findall("Input"):
            name = xml_input.get("name")
            _input[name] = self.build.get_config_tag_item("Input", name, "")

        self.json_config["Input"] = _input
        self.load()

    def save(self):
        """
        Save internal structures back to the build object, overwriting what is there.
        So if power charges are turned off, then no settings for power charges will be saved.
        """
        # Don't use self.build.properties, as we overwrite self.json_config["Input"] below
        # General.
        # pycharm rewrote this to a "dictionary literal"
        _input = {
            "resistancePenalty": self.win.combo_ResPenalty.currentData(),
            "bandit": self.win.combo_Bandits.currentData(),
            "pantheonMajorGod": self.win.combo_MajorPantheon.currentData(),
            "pantheonMinorGod": self.win.combo_MinorPantheon.currentData(),
            "igniteMode": self.win.combo_igniteMode.currentData(),
            "EHPUnluckyWorstOf": self.win.combo_EHPUnluckyWorstOf.currentData(),
            "usePowerCharges": self.win.check_PowerCharges.isChecked(),
            "overridePowerCharges": self.win.spin_NumPowerCharges.value(),
            "useFrenzyCharges": self.win.check_FrenzyCharges.isChecked(),
            "overrideFrenzyCharges": self.win.spin_NumFrenzyCharges.value(),
            "useEnduranceCharges": self.win.check_EnduranceCharges.isChecked(),
            "overrideEnduranceCharges": self.win.spin_NumEnduranceCharges.value(),
        }

        # ignoreJewelLimits

        # Combat
        # ToDo: This needs improvement to accomodate ItemSets and that the relevant item is active in an ItemSet
        if self.win.check_SiphoningCharges.isVisible():  # from Disintegrator
            _input["useSiphoningCharges"] = self.win.check_SiphoningCharges.isChecked()
            _input["overrideSiphoningCharges"] = self.win.spin_NumSiphoningCharges.value()
        if self.win.check_ChallengerCharges.isVisible():
            _input["useChallengerCharges"] = self.win.check_ChallengerCharges.isChecked()
            _input["overrideChallengerCharges"] = self.win.spin_NumChallengerCharges.value()
        if self.win.check_BlitzCharges.isVisible():
            _input["useBlitzCharges"] = self.win.check_BlitzCharges.isChecked()
            _input["overrideBlitzCharges"] = self.win.spin_NumBlitzCharges.value()
        # _input["multiplierGaleForce"] = self.win.xxx_xxx.value()
        # _input["overrideInspirationCharges"] = self.win.xxx_xxx.value()
        if self.win.check_GhostCharges.isVisible():
            _input["useGhostCharges"] = self.win.check_GhostCharges.isChecked()
            _input["overrideGhostCharges"] = self.win.spin_NumGhostCharges.value()
        # waitForMaxSeals

        # Will this produce "" or "~^" ???
        custom_mods = self.win.textedit_CustomModifiers.toPlainText().splitlines()
        if custom_mods:
            _input["customMods"] = "~^".join(custom_mods)

        self.json_config["Input"] = _input

    def initial_startup_setup(self):
        """Configure configuration tab widgets on startup"""
        # print("initial_startup_setup")
        self.win.label_NumPowerCharges.setVisible(False)
        self.win.spin_NumPowerCharges.setVisible(False)
        self.win.label_NumFrenzyCharges.setVisible(False)
        self.win.spin_NumFrenzyCharges.setVisible(False)
        self.win.label_NumEnduranceCharges.setVisible(False)
        self.win.spin_NumEnduranceCharges.setVisible(False)
        self.win.label_SiphoningCharges.setVisible(False)
        self.win.check_SiphoningCharges.setVisible(False)
        self.win.label_NumSiphoningCharges.setVisible(False)
        self.win.spin_NumSiphoningCharges.setVisible(False)
        self.win.label_ChallengerCharges.setVisible(False)
        self.win.check_ChallengerCharges.setVisible(False)
        self.win.label_NumChallengerCharges.setVisible(False)
        self.win.spin_NumChallengerCharges.setVisible(False)
        self.win.label_BlitzCharges.setVisible(False)
        self.win.check_BlitzCharges.setVisible(False)
        self.win.label_NumBlitzCharges.setVisible(False)
        self.win.spin_NumBlitzCharges.setVisible(False)
        self.win.label_GhostCharges.setVisible(False)
        self.win.check_GhostCharges.setVisible(False)
        self.win.label_NumGhostCharges.setVisible(False)
        self.win.spin_NumGhostCharges.setVisible(False)

        # ToDo: find things that need doing on other layouts that might get destroyed/recreated and repeat this exercise
        # Programatically set values on this layout as it will be destroyed and recreated in the Designer a lot
        general_layout: QGridLayout = self.win.label_ResPenalty.parent().layout()
        general_layout.setColumnMinimumWidth(0, 100)
        general_layout.setContentsMargins(0, 9, 3, 3)
        combat_layout: QGridLayout = self.win.label_PowerCharges.parent().layout()
        combat_layout.setColumnMinimumWidth(1, 50)
        combat_layout.setContentsMargins(0, 9, 3, 3)

        self.win.textedit_CustomModifiers.clear()


# def test() -> None:
#     config_ui = ConfigUI()
#     print(config_ui)


# if __name__ == "__main__":
#     test()
