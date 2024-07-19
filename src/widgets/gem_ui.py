"""
A class to show and manage the gem ui on the right hand side of the Skills tab.
"""

from copy import deepcopy

from PySide6.QtCore import QRect, Slot, QSize, Qt
from PySide6.QtGui import QColor, QBrush, QIcon
from PySide6.QtWidgets import QCheckBox, QComboBox, QListWidgetItem, QPushButton, QSpinBox, QWidget

from PoB.constants import ColourCodes, empty_gem_dict
from PoB.settings import Settings
from PoB.utils import _debug, bool_to_str, html_colour_text, print_call_stack, str_to_bool, index_exists
from widgets.ui_utils import set_combo_index_by_data


class GemUI(QWidget):
    """A class to manage one gem/skill on the right hand side of the UI"""

    def __init__(self, list_widget_item: QListWidgetItem, gems_by_name_or_id, parent_notify, _settings: Settings, gem=None) -> None:
        """
        init

        :param list_widget_item: QListWidgetItem: the item inthe list box that this instance is attached to.
        :param gems_by_name_or_id: dict: a dictionary of skills by id and name.
        :param parent_notify: function: function to call when a change has happened.
        :param _settings: A pointer to the settings.
        :param gem: ET.elementree: prefill with this gem.
        """
        super(GemUI, self).__init__()

        self.settings = _settings

        self.widget_height = 30
        self.setGeometry(0, 0, 620, self.widget_height)
        self.setMinimumHeight(self.widget_height)
        self.list_widget_item = list_widget_item
        # reference to the loaded json so we can get data for the selected gem
        self.gems_by_name_or_id = gems_by_name_or_id
        self.gem = gem
        if gem is None:
            self.gem = deepcopy(empty_gem_dict)
        self.parent_notify = parent_notify

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
        self.spin_gem_level.setValue(self.level)
        self.spin_gem_quality = QSpinBox(self)
        self.spin_gem_quality.setGeometry(360, 2, 50, 24)
        self.spin_gem_quality.setMaximum(40)
        self.spin_gem_quality.setValue(self.quality)
        self.combo_gem_variant = QComboBox(self)
        self.combo_gem_variant.setObjectName("combo_gem_variant")
        self.combo_gem_variant.addItem("Default", "Default")
        self.combo_gem_variant.setCurrentText(self.qualityId)
        # self.combo_gem_variant.addItem("Anomalous", "Alternate1")
        # self.combo_gem_variant.addItem("Divergent", "Alternate2")
        # self.combo_gem_variant.addItem("Phantasmal", "Alternate3")
        self.combo_gem_variant.setGeometry(420, 2, 90, 22)
        self.check_gem_enabled = QCheckBox(self)
        self.check_gem_enabled.setGeometry(530, 4, 20, 20)
        self.check_gem_enabled.setChecked(True)
        self.check_gem_enabled.setChecked(self.enabled)
        self.spin_gem_count = QSpinBox(self)
        self.spin_gem_count.setGeometry(570, 2, 50, 24)
        self.spin_gem_count.setMinimum(1)
        self.spin_gem_count.setMaximum(20)
        self.spin_gem_count.setVisible(False)
        self.spin_gem_count.setValue(self.count)

        self.coloured_text = ""  # html formatted name
        self.tags = []
        self.ggg_gem = None

        self.support = False
        self.colour = ""  # ColourCodes value
        self.levels = [{}]  # List of dict.
        self.max_reqDex = 0  # value from the json
        self.max_reqInt = 0  # value from the json
        self.max_reqStr = 0  # value from the json
        self.reqDex = 0
        self.reqInt = 0
        self.reqStr = 0
        self.naturalMaxLevel = 20
        self.stats_per_level = {}

        # needs to be a string as there are entries like "Limited to: 1 Survival"
        self.limited_to = ""
        # self._quality = 0
        self.unique_id = ""
        self.requires = {}
        self.influences = []
        self._armour = 0
        self.base_armour = 0  # value without quality and +nn additions/multipliers
        self._evasion = 0
        self.evasion_base_percentile = 0.0
        self.base_evasion = 0  # value without quality and +nn additions/multipliers
        self._energy_shield = 0
        self.energy_shield_base_percentile = 0.0
        self.base_energy_shield = 0  # value without quality and +nn additions/multipliers
        self.armour_base_percentile = 0.0

        """
        new
        gemId="Metadata/Items/Gems/SupportGemFeedingFrenzy" 	<-skillId
        variantId="FeedingFrenzySupport" 						<-Dict Key
        skillId="SupportMinionOffensiveStance" 					<-grantedEffectId
        nameSpec="Feeding Frenzy"								<-grantedEffect.name

        old
        gemId="Metadata/Items/Gems/SupportGemImpendingDoom"		<-skillId
        skillId="ViciousHexSupport"								<-Dict Key
        nameSpec="Impending Doom"								<-grantedEffect.name
        """

        self.set_triggers()
        # the call to fill_gem_list() will set the current gem name in the combo_gem_list widget.
        # doing this now wouldn't work as the combobox isn't full.

    def __del__(self):
        """
        Remove PySide elements, prior to being deleted.
        The frame appears not to have a list of children, only layouts.
        Disconnect triggers so they aren't occuring during deletion.

        :return: N/A
        """
        # Remove triggers and don't be put off by errors
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
    def nameSpec(self) -> str:
        # nameSpec
        return self.gem.get("nameSpec", "")

    @nameSpec.setter
    def nameSpec(self, new_value):
        self.gem["nameSpec"] = new_value

    @property
    def level(self) -> int:
        return self.gem.get("level", 1)

    @level.setter
    def level(self, new_value):
        self.gem["level"] = new_value
        self.spin_gem_level.setValue(new_value)

    @property
    def quality(self) -> int:
        return self.gem.get("quality", 0)

    @quality.setter
    def quality(self, new_value):
        self.gem["quality"] = new_value
        self.spin_gem_quality.setValue(new_value)

    @property
    def qualityId(self) -> str:
        return self.gem.get("qualityId", "")

    @qualityId.setter
    def qualityId(self, new_value):
        self.gem["qualityId"] = new_value
        set_combo_index_by_data(self.combo_gem_variant, new_value)

    # @property
    # def skillId(self) -> str:
    #     return self.gem.get("skillId", "")
    #
    # @skillId.setter
    # def skillId(self, new_value):
    #     self.gem["skillId"] = new_value

    @property
    def enabled(self) -> bool:
        return self.gem.get("enabled", True)

    @enabled.setter
    def enabled(self, new_value):
        self.gem["enabled"] = new_value
        self.check_gem_enabled.setChecked(new_value)

    @property
    def enableGlobal1(self) -> bool:
        return self.gem.get("enableGlobal1", True)

    @enableGlobal1.setter
    def enableGlobal1(self, new_value):
        self.gem["enableGlobal1"] = new_value

    @property
    def enableGlobal2(self) -> bool:
        return self.gem.get("enableGlobal2", True)

    @enableGlobal2.setter
    def enableGlobal2(self, new_value):
        self.gem["enableGlobal2"] = new_value

    @property
    def count(self) -> int:
        return self.gem.get("count", 1)

    @count.setter
    def count(self, new_value):
        self.gem["count"] = new_value
        self.spin_gem_count.setValue(new_value)

    @property
    def variantId(self) -> str:
        """
        Needed so we can have a setter function.

        :return: str: The name of this gem
        """
        return self.gem.get("variantId", "")

    @variantId.setter
    def variantId(self, new_value):
        """
        Actions when the variantId / combo_gem_list changes.

        :param new_value: str
        :return: N/A
        """
        self.btn_GemRemove.setEnabled(new_value != "")
        self.spin_gem_count.setVisible("Support" not in new_value)
        if new_value == "":
            return
        try:
            self.ggg_gem = self.gems_by_name_or_id[new_value]
            self.coloured_text = self.ggg_gem.get("coloured_text")
            # set the editbox portion of combobox to the correct colour
            colour = self.ggg_gem.get("colour", ColourCodes.NORMAL.value)
            self.combo_gem_list.setStyleSheet(f"QComboBox:!editable {{color: {colour}}}")

            # If the comboBox was empty before calling this function, then return
            if self.gem is None:
                return
            self.gem["variantId"] = new_value
            self.nameSpec = self.combo_gem_list.currentText()
            self.gem["skillId"] = self.ggg_gem["grantedEffectId"]

            self.support = self.ggg_gem.get("support", False)
            self.levels.append(self.ggg_gem["grantedEffect"]["levels"])
            self.max_reqDex = self.ggg_gem.get("reqDex", 0)
            self.max_reqInt = self.ggg_gem.get("reqInt", 0)
            self.max_reqStr = self.ggg_gem.get("reqStr", 0)
            self.naturalMaxLevel = self.ggg_gem.get("naturalMaxLevel", 20)

        except KeyError:
            print("Error in variantId: variantId setter.")
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
        load the UI elements from the json dict
        :return: N/A
        """
        print(f"gem_ui: load: {gem=}")
        self.gem = gem
        self.spin_gem_level.setValue(self.level)
        self.spin_gem_quality.setValue(self.quality)
        self.spin_gem_count.setValue(self.count)
        self.check_gem_enabled.setChecked(self.enabled)
        self.combo_gem_variant.setCurrentText(self.qualityId)
        self.set_triggers()
        self.combo_gem_list.setCurrentText(gem["nameSpec"])

    @Slot()
    def save(self, notify=True):
        """
        Save the UI elements into the json dict
        This is called by all the elements in this class, including combo_gem_list_changed, so don't set variantId.

        :param notify: bool: If True use call back.
        :return N/A
        """
        # This stops an empty gem saving
        if self.variantId == "":
            return
        self.level = self.spin_gem_level.value()
        self.quality = self.spin_gem_quality.value()
        self.count = self.spin_gem_count.value()
        self.enabled = self.check_gem_enabled.isChecked()
        self.qualityId = self.combo_gem_variant.currentData()

        if notify:
            self.parent_notify(self.list_widget_item)

        # print(f"gem_ui: save: {self.gem=}")
        return self.gem

    @Slot()
    def combo_gem_list_changed(self, item, notify=True):
        """
        Triggered when the gem list combo is changed.

        :param item: str: Text from comboBox
        :param notify: bool: If True use call back when calling save
        :return N/A
        """
        # Set a value. When first run, save will not activate if skillId is empty
        if item == "":
            return
        # print(f"combo_gem_list_changed, {item=}, {self.combo_gem_list.currentData()=}")
        self.variantId = self.combo_gem_list.currentData()
        self.save(notify)
        if index_exists(self.gems_by_name_or_id, self.variantId):
            gem = self.gems_by_name_or_id[self.variantId]
            self.combo_gem_list.setToolTip(f'<font color={gem["colour"]}>{gem["grantedEffect"]["description"]}</font>')

    def fill_gem_list(self, base_gems, show_support_gems):
        """
        File the gem list combo. This is called separately as we need the show_support_gems value from SkillsUI()

        :param base_gems: a list of curated gems available
        :param show_support_gems: str: "All", "Normal" and "Awakened"
        :return:
        """

        def add_colour(index):
            """
            Add colour to a gem name.

            :param index: int: Index into the combolist
            :return: N/A
            """
            colour = g.get("colour", ColourCodes.NORMAL.value)
            self.combo_gem_list.setItemData(index, QBrush(colour), Qt.ForegroundRole)

        if show_support_gems == "Awakened":
            for variantId, g in base_gems.items():
                display_name = g["base_item"]["display_name"]
                if "Awakened" in display_name:
                    self.combo_gem_list.addItem(display_name, variantId)
                    add_colour(self.combo_gem_list.count() - 1)
        else:
            for variantId, g in base_gems.items():
                display_name = g["grantedEffect"]["name"]
                if show_support_gems == "Normal" and "Awakened" in display_name:
                    continue
                self.combo_gem_list.addItem(display_name, userData=variantId)
                add_colour(self.combo_gem_list.count() - 1)

        # set the ComboBox dropdown width.
        self.combo_gem_list.view().setMinimumWidth(self.combo_gem_list.minimumSizeHint().width())
        # ToDo: Sort by other methods
        # Sort Alphabetically
        self.combo_gem_list.model().sort(0)
        if self.gem is not None and self.variantId != "":
            # self.combo_gem_list.setCurrentIndex(set_combo_index_by_data(self.combo_gem_list, self.skillId))
            self.combo_gem_list.setCurrentText(self.nameSpec)
            self.combo_gem_list_changed(self.nameSpec, False)
        else:
            self.combo_gem_list.setCurrentIndex(-1)

        # Setup trigger to save information back to the json dict
        self.combo_gem_list.currentTextChanged.connect(self.combo_gem_list_changed)


# def test() -> None:
#     skills_ui = SkillsUI()
#     print(skills_ui)
#
#
# if __name__ == "__main__":
#     test()
