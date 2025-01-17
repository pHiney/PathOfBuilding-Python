"""
A class to encapsulate one gem/skill
"""

from copy import deepcopy

from PoB.constants import bad_text, pob_debug, ColourCodes, empty_gem_dict, quality_id
from PoB.settings import Settings
from PoB.mod import Mod
from PoB.utils import _debug, html_colour_text, index_exists, str_to_bool, bool_to_str
from widgets.ui_utils import search_stats_list_for_regex

colours = (
    ColourCodes.NORMAL.value,
    ColourCodes.STRENGTH.value,
    ColourCodes.DEXTERITY.value,
    ColourCodes.INTELLIGENCE.value,
    ColourCodes.WHITE.value,
)


class Gem:
    def __init__(self, _settings: Settings, pob_gem) -> None:
        """
        Initialise defaults
        :param _settings: A pointer to the settings.
        :param: pob_gem: dict from build.
        """
        self.settings = _settings
        # This gem's entry from gems.json
        self.base_gem = None
        self.name = ""
        self._type = ""  # or item_class - eg weapon
        self.sub_type = ""  # or item_class - eg claw
        self.active = False  # is this the item that is currently chosen/shown in the dropdown ?

        self.gem = pob_gem
        if self.gem is None:
            self.gem = deepcopy(empty_gem_dict)

        # This is not always available from the json character download
        self.level_req = 0

        self.id = 0
        self.rarity = "NORMAL"
        self._level = 1
        # self.enabled = True
        # self.quality = self.settings.default_gem_quality
        # self.count = 1
        self.support = False
        self.qualityVariant = "Default"
        self.minion = False
        # self.skillMinionSkillCalcs = 0
        # self.skillMinionCalcs = ""
        # self.skillMinionSkill = 0
        # self.skillMinion = ""

        self.colour = ""  # ColourCodes value
        self.coloured_name = ""  # html formatted name
        self.levels = [{}]  # List of dict.
        self.max_reqDex = 0  # value from the json: reqDex
        self.max_reqInt = 0  # value from the json: reqInt
        self.max_reqStr = 0  # value from the json: reqStr
        self.reqDex = 0
        self.reqInt = 0
        self.reqStr = 0
        self.naturalMaxLevel = 20
        self.curr_level_info = {}

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

    @property
    def level(self) -> int:
        return self.gem.get("level", 1)

    @level.setter
    def level(self, new_level):
        """Set things like armour damage, required stats based on the level"""
        self._level = new_level
        self.curr_level_info = self.levels[new_level]
        self.level_req = self.curr_level_info.get("levelRequirement",0)
        if self.max_reqDex:
            self.reqDex = self.gem_stat_requirement(new_level, self.max_reqDex)
        if self.max_reqInt:
            self.reqInt = self.gem_stat_requirement(new_level, self.max_reqInt)
        if self.max_reqStr:
            self.reqStr = self.gem_stat_requirement(new_level, self.max_reqStr)

    @property
    def enabled(self) -> bool:
        return self.gem.get("count", True)

    @enabled.setter
    def enabled(self, new_value):
        self.gem["count"] = new_value

    @property
    def nameSpec(self) -> str:
        return self.gem.get("nameSpec", "")

    @nameSpec.setter
    def nameSpec(self, new_value):
        self.gem["nameSpec"] = new_value

    @property
    def skillId(self) -> str:
        return self.gem.get("skillId", "")

    @skillId.setter
    def skillId(self, new_value):
        self.gem["skillId"] = new_value

    @property
    def variantId(self) -> str:
        return self.gem.get("variantId", "")

    @variantId.setter
    def variantId(self, new_value):
        self.gem["variantId"] = new_value

    @property
    def quality(self) -> int:
        return self.gem.get("quality", self.settings.default_gem_quality)

    @quality.setter
    def quality(self, new_value):
        self.gem["quality"] = new_value

    @property
    def qualityId(self) -> str:
        return self.gem.get("qualityId", "Default")

    @quality.setter
    def quality(self, new_value):
        self.gem["qualityId"] = new_value

    @property
    def count(self) -> int:
        return self.gem.get("count", 1)

    @count.setter
    def count(self, new_value):
        self.gem["count"] = new_value

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
    def gemId(self) -> str:
        return self.gem.get("gemId", "")

    @gemId.setter
    def gemId(self, new_value):
        self.gem["gemId"] = new_value

    @property
    def skillMinionSkillCalcs(self) -> int:
        return self.gem.get("skillMinionSkillCalcs", 1)

    @skillMinionSkillCalcs.setter
    def skillMinionSkillCalcs(self, new_value):
        if new_value:
            self.gem["skillMinionSkillCalcs"] = new_value
        else:
            self.gem.pop("skillMinionSkillCalcs", 0)

    @property
    def skillMinionCalcs(self) -> int:
        return self.gem.get("skillMinionCalcs", 1)

    @skillMinionCalcs.setter
    def skillMinionCalcs(self, new_value):
        if new_value:
            self.gem["skillMinionCalcs"] = new_value
        else:
            self.gem.pop("skillMinionCalcs", 0)

    @property
    def skillMinionSkill(self) -> str:
        return self.gem.get("skillMinionSkill", "")

    @skillMinionSkill.setter
    def skillMinionSkill(self, new_value):
        if new_value:
            self.gem["skillMinionSkill"] = new_value
        else:
            self.gem.pop("skillMinionSkill", "")

    @property
    def skillMinion(self) -> str:
        return self.gem.get("skillMinion", "")

    @skillMinion.setter
    def skillMinion(self, new_value):
        if new_value:
            self.gem["skillMinion"] = new_value
        else:
            self.gem.pop("skillMinion", "")

    def load_from_ggg_json(self, json_gem, gems_by_name_or_id):
        """
        Load gem from GGG. This should be called after load_base_gem_json so it can load the defaults.
        :param json_gem: This gem from the imported json.
        :param gems_by_name_or_id: list of gems from gems.json.
        :return: gem's xml
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

        self.gem.set("level", get_property(json_gem, "Level", "1"))
        self.gem.set("quality", get_property(json_gem, "Quality", "0"))
        q = json_gem.get("typeLine", "Anomalous")
        self.gem.set("qualityId", quality_id[q])

        return self.gem

    def load_base_gem_json(self, json_gem):
        """

        :param json_gem:
        :return: xml version of the gem
        """
        self.base_gem = json_gem
        self.name = json_gem["grantedEffect"]["name"]
        self.support = json_gem.get("support", False)
        self.colour = colours[json_gem.get("colour", 0)]
        self.coloured_name = html_colour_text(self.colour, self.name)
        self.levels.append(json_gem["grantedEffect"]["levels"]) # the first entry of a list in Python is 0, so we append the json info
        self.max_reqDex = json_gem.get("reqDex", 0)
        self.max_reqInt = json_gem.get("reqInt", 0)
        self.max_reqStr = json_gem.get("reqStr", 0)
        self.naturalMaxLevel = json_gem.get("naturalMaxLevel", 20)

        return self.gem

    def load(self, gem):
        """
        Load gem from build. This should be called after load_base_gem_json so that it can load the defaults.
        :param: gem
        :return: N/A
        """
        self.gem = gem
        self.gem.set("gemId", self.base_gem.get("skillId", ""))
        self.gem.set("skillId", self.base_gem["grantedEffectId"])
        self.gem.set("variantId", self.base_gem["grantedEffectId"])

    def save(self, xml=False):
        """Save"""
        return self.gem

    def gem_stat_requirement(self, gem_level, required_stat):
        """
        -- From PyPoE's formula.py
        Calculates and returns the stat requirement for the specified level requirement.

        The calculations vary depending on the gem type (i.e. active or support gem) and on the multiplier.

        Currently only multipliers of 100, 60 and 40 are supported. (These come from reqDex/reqStr/reqInt in base_gems.json)
        :param gem_level: int: Level requirement for the current gem level
        :param required_stat: Stat multiplier, i.e. from SkillGems.dat (eg: reqStr = 100)
        :return: int: calculated stat requirement
        """
        if self.support:
            b = 6 * required_stat / 100
            match required_stat:
                case 100:
                    a = 1.495
                case 60:
                    a = 0.945  # 1.575 * 0.6
                case 40:
                    a = 0.6575  # 1.64375 * 0.6
                case _:
                    return 0
        else:
            b = 8 * required_stat / 100
            match required_stat:
                case 100:
                    a = 2.1
                    b = 7.75
                case 75:
                    a = 1.619
                case 60:
                    a = 1.325
                case 40:
                    a = 0.924
                case _:
                    return 0

        result = round(gem_level * a + b)
        # Gems seem to have no requirements lower then 14
        return 0 if result < 14 else result
