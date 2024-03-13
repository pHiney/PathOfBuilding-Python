"""
A class to show and manage the gem ui on the right hand side of the Skills tab.
"""

import xml.etree.ElementTree as ET

from PySide6.QtCore import QRect, Slot, QSize, Qt
from PySide6.QtGui import QColor, QBrush, QIcon
from PySide6.QtWidgets import QCheckBox, QComboBox, QPushButton, QSpinBox, QWidget

from PoB.constants import ColourCodes, empty_gem_xml, empty_gem_dict
from PoB.gem import Gem
from widgets.ui_utils import (
    _debug,
    str_to_bool,
    bool_to_str,
    print_a_xml_element,
    print_call_stack,
    set_combo_index_by_data,
)


class GemUI(QWidget):
    """
    A class to manage one gem/skill on the right hand side of the UI
    """

    def __init__(self, my_list_item, json_gems, parent_notify, gem=None) -> None:
        """
        init

        :param my_list_item:QListWidgetItem: the item inthe list box that this instance is attached to
        :param json_gems: dict: a dictionary of skills by id and name
        :param parent_notify: function: function to call when a change has happened
        :param gem: ET.elementree: prefill with this gem
        """
        super(GemUI, self).__init__()

        self.widget_height = 30
        self.setGeometry(0, 0, 620, self.widget_height)
        self.setMinimumHeight(self.widget_height)
        self.my_list_item = my_list_item
        # reference to the loaded json so we can get data for the selected gem
        self.ggg_gem_list = json_gems
        if gem is None:
            gem = empty_gem_dict
        self.pob_gem = gem
        self.parent_notify = parent_notify

        self.coloured_text = ""
        self.tags = []
        self.ggg_gem = None

        # def setupUi(self, gem_list, show_support_gems):
        self.btn_GemRemove = QPushButton(self)
        self.btn_GemRemove.setGeometry(QRect(4, 4, 22, 22))
        cross_icon = QIcon()
        cross_icon.addFile(":/Art/Icons/cross.png", QSize(), QIcon.Normal, QIcon.Off)
        self.btn_GemRemove.setIcon(cross_icon)
        self.combo_gem_list = QComboBox(self)
        self.combo_gem_list.setGeometry(30, 3, 260, 22)
        self.combo_gem_list.setDuplicatesEnabled(False)
        self.combo_gem_list.setMaxVisibleItems(15)
        self.spin_gem_level = QSpinBox(self)
        self.spin_gem_level.setGeometry(300, 2, 50, 24)
        self.spin_gem_level.setMinimum(1)
        self.spin_gem_level.setMaximum(20)
        self.spin_gem_quality = QSpinBox(self)
        self.spin_gem_quality.setGeometry(360, 2, 50, 24)
        self.spin_gem_quality.setMaximum(40)
        self.combo_gem_variant = QComboBox(self)
        self.combo_gem_variant.setObjectName("combo_gem_variant")
        self.combo_gem_variant.addItem("Default", "Default")
        # self.combo_gem_variant.addItem("Anomalous", "Alternate1")
        # self.combo_gem_variant.addItem("Divergent", "Alternate2")
        # self.combo_gem_variant.addItem("Phantasmal", "Alternate3")
        self.combo_gem_variant.setGeometry(420, 2, 90, 22)
        self.check_gem_enabled = QCheckBox(self)
        self.check_gem_enabled.setGeometry(530, 4, 20, 20)
        self.check_gem_enabled.setChecked(True)
        self.spin_gem_count = QSpinBox(self)
        self.spin_gem_count.setGeometry(570, 2, 50, 24)
        self.spin_gem_count.setMinimum(1)
        self.spin_gem_count.setMaximum(20)
        self.spin_gem_count.setVisible(False)

        self.load(self.pob_gem)
        # self.fill_gem_list(json_gems, show_support_gems)

    def __del__(self):
        """
        Remove PySide elements, prior to being deleted.
        The frame appears not to have a list of children, only layouts.
        Disconnect triggers so they aren't occuring during deletion.

        :return: N/A
        """
        # Remove triggers
        try:
            self.spin_gem_level.valueChanged.disconnect(self.save)
        except RuntimeError:
            pass
        try:
            self.spin_gem_quality.valueChanged.disconnect(self.save)
        except RuntimeError:
            pass
        try:
            self.spin_gem_count.valueChanged.disconnect(self.save)
        except RuntimeError:
            pass
        try:
            self.check_gem_enabled.stateChanged.disconnect(self.save)
        except RuntimeError:
            pass
        try:
            self.combo_gem_variant.currentTextChanged.disconnect(self.save)
        except RuntimeError:
            pass
        try:
            self.combo_gem_list.currentTextChanged.disconnect(self.combo_gem_list_changed)
        except RuntimeError:
            pass

    def sizeHint(self) -> QSize:
        """Return a known size. Without this the default row height is about 22"""
        return QSize(620, self.widget_height)

    @property
    def name(self):
        # nameSpec
        return self.pob_gem.get("name", "")

    @name.setter
    def name(self, new_value):
        self.pob_gem["name"] = new_value

    @property
    def level(self):
        return self.pob_gem.get("level", "")

    @level.setter
    def level(self, new_value):
        self.pob_gem["level"] = new_value
        self.spin_gem_level.setValue(new_value)

    @property
    def quality(self):
        return self.pob_gem.get("quality", "")

    @quality.setter
    def quality(self, new_value):
        self.pob_gem["quality"] = new_value
        self.spin_gem_quality.setValue(new_value)

    @property
    def qualityId(self):
        return self.pob_gem.get("qualityId", "")

    @qualityId.setter
    def qualityId(self, new_value):
        self.pob_gem["qualityId"] = new_value
        set_combo_index_by_data(self.combo_gem_variant, new_value)

    @property
    def enabled(self):
        return self.pob_gem.get("enabled", True)

    @enabled.setter
    def enabled(self, new_value):
        self.pob_gem["enabled"] = new_value
        self.check_gem_enabled.setChecked(new_value)

    @property
    def enableGlobal1(self):
        return self.pob_gem.get("enableGlobal1", True)

    @enableGlobal1.setter
    def enableGlobal1(self, new_value):
        self.pob_gem["enableGlobal1"] = new_value

    @property
    def enableGlobal2(self):
        return self.pob_gem.get("enableGlobal2", True)

    @enableGlobal2.setter
    def enableGlobal2(self, new_value):
        self.pob_gem["enableGlobal2"] = new_value

    @property
    def count(self):
        return self.pob_gem.get("count", 1)

    @count.setter
    def count(self, new_value):
        self.pob_gem["count"] = new_value
        self.spin_gem_count.setValue(new_value)

    @property
    def skill_id(self):
        """
        Needed so we can have a setter function.

        :return: str: The name of this gem
        """
        return self.pob_gem.get("skillId")

    @skill_id.setter
    def skill_id(self, new_value):
        """
        Actions when the skill_id changes.

        :param new_value: str
        :return:
        """
        self.btn_GemRemove.setEnabled(new_value != "")
        self.spin_gem_count.setVisible("Support" not in new_value)
        if new_value == "":
            return
        try:
            self.ggg_gem = self.ggg_gem_list[new_value]
            self.coloured_text = self.ggg_gem.get("coloured_text")
            # set the editbox portion of combobox to the correct colour
            colour = self.ggg_gem.get("colour", ColourCodes.NORMAL.value)
            self.combo_gem_list.setStyleSheet(f"QComboBox:!editable {{color: {colour}}}")

            # If the comboBox was empty before calling this function, then return
            if self.pob_gem is None:
                return
            self.pob_gem["skillId"] = new_value
            if self.combo_gem_list.currentText():
                self.pob_gem["name"] = self.combo_gem_list.currentText()
        except KeyError:
            pass

    def set_triggers(self):
        """Setup triggers to save information back the dict"""
        self.spin_gem_level.valueChanged.connect(self.save)
        self.spin_gem_quality.valueChanged.connect(self.save)
        self.spin_gem_count.valueChanged.connect(self.save)
        self.check_gem_enabled.stateChanged.connect(self.save)
        self.combo_gem_variant.currentTextChanged.connect(self.save)

    def load(self, gem):
        """
        load the UI elements from the xml element
        :return: N/A
        """
        self.pob_gem = gem
        self.set_triggers()

    @Slot()
    def save(self, notify=True):
        """
        Save the UI elements into the xml element
        This is called by all the elements in this class

        :param: notify: bool: If true don't use call back
        :return: N/A
        """
        # This stops an empty gem saving to the xml
        if self.skill_id == "":
            return
        if self.pob_gem is None:
            self.pob_gem = ET.fromstring(empty_gem_xml)
        self.level = self.spin_gem_level.value()
        self.quality = self.spin_gem_quality.value()
        self.count = self.spin_gem_count.value()
        self.enabled = bool_to_str(self.check_gem_enabled.isChecked())
        self.qualityId = self.combo_gem_variant.currentData()
        self.skill_id = self.combo_gem_list.currentData()

        if notify:
            self.parent_notify(self.my_list_item)

    def load_from_xml(self, gem):
        """
        load the UI elements from the xml element
        :return: N/A
        """
        # print(print_a_xml_element(gem))
        if gem is not None:
            self.pob_gem = empty_gem_xml
            self.level = int(gem.get("level", 1))
            self.quality = int(gem.get("quality", 0))
            self.count = gem.get("count", 1) == "nil" and 1 or int(gem.get("count"))
            self.enabled = str_to_bool(gem.get("enabled"))
            self.qualityId = gem.get("qualityId", "Default")
            self.skill_id = gem.get("skillId")

        self.set_triggers()

    def save_to_xml(self):
        """
        Save the UI elements into the xml element
        This is called by all the elements in this class

        :param: notify: bool: If true don't use call back
        :return: ET.xml snippet
        """
        # This stops an empty gem saving to the xml
        xml_gem = ET.fromstring(empty_gem_xml)
        if self.skill_id == "":
            return
        # ToDO: fix
        xml_gem.set("level", str(self.spin_gem_level.value()))
        xml_gem.set("quality", str(self.spin_gem_quality.value()))
        xml_gem.set("count", str(self.spin_gem_count.value()))
        xml_gem.set("enabled", bool_to_str(self.check_gem_enabled.isChecked()))
        xml_gem.set("qualityId", self.combo_gem_variant.currentData())
        xml_gem.set("skill_id", self.combo_gem_list.currentData())

    @Slot()
    def combo_gem_list_changed(self, item):
        """
        Triggered when the gem list combo is changed.

        :param item: str:
        :return: N/A
        """
        # print(f"combo_gem_list_changed, {item=}")
        if item == "":
            return
        # Set a value. When first run, save will not activate if skill_id is empty
        self.skill_id = self.ggg_gem_list[item]["skillId"]
        self.save()

    def fill_gem_list(self, gem_list, show_support_gems):
        """
        File the gem list combo

        :param gem_list: a list of curated gems available
        :param show_support_gems: if True, only add non-awakened gems
        :return:
        """

        def add_colour(index):
            """
            Add colour to a gem name.

            :param index: int: Index into the combolist
            :return: N/A
            """
            colour = gem_list[g].get("colour", ColourCodes.NORMAL.value)
            self.combo_gem_list.setItemData(index, QBrush(colour), Qt.ForegroundRole)

        if show_support_gems == "Awakened":
            for g in gem_list:
                display_name = gem_list[g]["base_item"]["display_name"]
                if "Awakened" in display_name:
                    self.combo_gem_list.addItem(display_name, g)
                    add_colour(self.combo_gem_list.count() - 1)
        else:
            for g in gem_list:
                display_name = gem_list[g]["grantedEffect"]["name"]
                if show_support_gems == "Normal" and "Awakened" in display_name:
                    continue
                self.combo_gem_list.addItem(display_name, g)
                add_colour(self.combo_gem_list.count() - 1)

        # set the ComboBox dropdown width.
        self.combo_gem_list.view().setMinimumWidth(self.combo_gem_list.minimumSizeHint().width())
        # ToDo: Sort by other methods
        # Sort Alphabetically
        self.combo_gem_list.model().sort(0)
        if self.pob_gem is not None and self.skill_id != "":
            self.combo_gem_list.setCurrentIndex(set_combo_index_by_data(self.combo_gem_list, self.skill_id))
        else:
            self.combo_gem_list.setCurrentIndex(-1)

        # Setup trigger to save information back the the xml object
        self.combo_gem_list.currentTextChanged.connect(self.combo_gem_list_changed)


# def test() -> None:
#     skills_ui = SkillsUI()
#     print(skills_ui)
#
#
# if __name__ == "__main__":
#     test()
