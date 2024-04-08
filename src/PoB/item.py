"""
A class to encapsulate one item
"""

from copy import deepcopy
import math
import re

from PoB.constants import (
    ColourCodes,
    bad_text,
    empty_item_dict,
    influencers,
    influence_colours,
    pob_debug,
    slot_map,
    slot_names,
    weapon_classes,
)
from PoB.settings import Settings
from PoB.mod import Mod
from PoB.utils import _debug, html_colour_text, index_exists, str_to_bool, bool_to_str
from PoB.pob_xml import print_a_xml_element
from widgets.ui_utils import search_stats_list_for_regex


class Item:
    def __init__(self, _settings: Settings, _base_items, _slot=None) -> None:
        """
        Initialise defaults
        :param _settings: A pointer to the settings
        :param _base_items: dict: the loaded base_items.json
        :param _slot: where this item is worn/carried.
        """
        self._slot = _slot
        # the dict from json of the all items
        self.base_items = _base_items
        self.settings = _settings
        # This item's entry from base_items
        self.base_item = None
        self.name = ""  # Combination of title and base_name
        self.type = ""
        self.sub_type = ""  # Evasion/Energy Shield, Armour, Utility, Talisman, etc. Or weapon type for weapons
        self.weapon_sub_type = ""  # Rune, Thrusting, Warstaff
        self.active = False  # Is this the item that is currently chosen/shown in the dropdown ?
        self.pob_item = deepcopy(empty_item_dict)
        self.variants = self.pob_item.setdefault("Variants", [])
        # list of things like evasion=100 ilevel=44
        self.attribs = self.pob_item["Attribs"]
        # list of things like str=100  Level=41
        self.requires = self.pob_item["Requires"]

        # this is not always available from the json character download
        self.level_req = 0

        # self.id = 0
        # self.rarity = "NORMAL"
        self.ilevel = 0
        # needs to be a string as there are entries like "Limited to: 1 Survival"
        self.limited_to = ""
        self._quality = 0
        self.influences = []
        self.two_hand = False
        self.corrupted = False
        self.abyss_jewel = None
        self.synthesised = None
        self.properties = {}
        # implicit/explicit mods affecting this item with current variants
        self.implicitMods = []
        self.explicitMods = []
        # all implicit/explicit mods including all variants
        self.full_implicitMods_list = []
        self.full_explicitMods_list = []
        # self.craftedMods = []
        self.enchantMods = []
        self.fracturedMods = []
        self.crucibleMods = []
        self.active_mods = []
        self.all_stats = []
        self.slots = []

        # Some items have a smaller number of variants than the actual variant lists. Whilst these need to be fixed, this will get around it.
        self.max_variant = 0
        # names of the variants
        self.variant_names = [""]  # Variants are numbered from one
        # self.variant_names.append("")
        # dict of lists of the variant entries (EG: base_name, influences, etc'
        self.variant_entries = {}
        # I think i need to store the variants separately, for crafting. Dict of string lists, var number is index
        self.variantMods = {}

        self.base_armour = 0  # value without quality and +nn additions/multipliers
        self._armour = 0
        self._evasion = 0
        self._energy_shield = 0
        self.evasion_base_percentile = 0.0
        self.base_evasion = 0  # value without quality and +nn additions/multipliers
        self.energy_shield_base_percentile = 0.0
        self.base_energy_shield = 0  # value without quality and +nn additions/multipliers
        self.armour_base_percentile = 0.0
        self.radius = ""
        # tooltip text for the item stats, not DPS. Prevent recalculating mostly static values every time the TT is read
        self.base_tooltip_text = ""

        # special dictionary/list for the rare template items that get imported into a build
        self.crafted_item = {"Prefix": [], "Suffix": []}
        self.alt_variants = {}

        self.rarity_colour = ""
        self.grants_skill = []
        self.grants_skill_level = []

    @property
    def id(self) -> int:
        return self.pob_item.get("id", 0)

    @id.setter
    def id(self, new_value):
        self.pob_item["id"] = int(new_value)

    @property
    def base_name(self) -> str:
        return self.pob_item.get("base_name", "")

    @base_name.setter
    def base_name(self, new_value):
        # remove any (information)  EG: 'Two-Stone Ring (Cold/Lightning)'
        m = re.search(r"(.*)( \(.*\))$", new_value)
        if m:
            new_value = m.group(1)
        self.pob_item["base_name"] = new_value
        self.name = f'{self.title and f"{self.title}, " or ""}{new_value}'
        # Look up base_items to get the item type
        self.base_item = self.base_items.get(new_value, None)
        if self.base_item is not None:
            self.type = self.base_item["type"]
            self.sub_type = self.base_item.get("subType", "")
            # setup weapon's subType
            if self.type in weapon_classes:
                if self.sub_type != "":
                    self.weapon_sub_type = self.sub_type  # This will be something like "Thrusting"
                self.sub_type = self.type
                self.type = "Weapon"
                self.two_hand = "twohand" in self.base_item["tags"]

            # check for any extra requires. Just attributes for now.
            reqs = self.base_item.get("req", None)
            if reqs:
                for tag in reqs:
                    match tag:
                        case "Dex" | "Int" | "Str" | "Level":
                            val = reqs.get(tag, bad_text)
                            # don't overwrite a current value
                            if self.requires.get(tag, bad_text) == bad_text and val != bad_text and val != 0:
                                self.requires[tag] = val
        # elif "Flask" in new_value:
        #     self.type = "Flask"
        #     self.sub_type = "Flask"

        match self.type:
            case "Shield":
                self.slots = ["Weapon 2", "Weapon 2 Swap"]
            case "Weapon":
                if self.two_hand:
                    self.slots = ["Weapon 1", "Weapon 1 Swap"]
                else:
                    # Put primary weapons before alt weapons for auto filling of item slots
                    self.slots = [
                        "Weapon 1",
                        "Weapon 2",
                        "Weapon 1 Swap",
                        "Weapon 2 Swap",
                    ]
            case "Ring":
                self.slots = ["Ring 1", "Ring 2"]
            case "Flask":
                self.slots = ["Flask 1", "Flask 2", "Flask 3", "Flask 4", "Flask 5"]
            case _:
                self.slots = [self.type]

    @property
    def title(self) -> str:
        return self.pob_item.get("title", "")

    @title.setter
    def title(self, new_value):
        self.pob_item["title"] = new_value
        self.name = f'{new_value and f"{new_value}, " or ""}{self.base_name}'

    @property
    def rarity(self) -> str:
        return self.pob_item.get("Rarity", "")

    @rarity.setter
    def rarity(self, new_value):
        self.pob_item["Rarity"] = new_value
        self.rarity_colour = ColourCodes[new_value].value

    @property
    def sockets(self) -> str:
        return self.get_attrib("Sockets", "")

    @sockets.setter
    def sockets(self, new_value):
        self.set_attrib("Sockets", new_value)

    @property
    def league(self) -> str:
        return self.get_attrib("League", "")

    @league.setter
    def league(self, new_value):
        self.set_attrib("League", new_value)

    @property
    def source(self) -> str:
        return self.pob_item.get("Source", "")

    @source.setter
    def source(self, new_value):
        self.set_attrib("Source", new_value)

    @property
    def corrupted(self) -> bool:
        return self.pob_item.get("corrupted", False)

    @corrupted.setter
    def corrupted(self, new_value):
        if new_value:
            self.pob_item["corrupted"] = new_value
        else:
            self.pob_item.pop("corrupted", False)

    @property
    def current_variant(self) -> int:
        """variants are numbered from 1, so 0 is no selection."""
        return self.pob_item.get("Selected Variant", 0)

    @current_variant.setter
    def current_variant(self, new_value):
        new_value = int(new_value)
        if new_value:
            self.pob_item["Selected Variant"] = new_value
        else:
            self.pob_item.pop("Selected Variant", 0)

    @property
    def abyssal_sockets(self):
        return [char for char in " " + self.sockets if char == "A"]

    @property
    def coloured_text(self) -> str:
        return html_colour_text(self.rarity_colour, f"{self.name}")

    @property
    def slot(self) -> str:
        return self._slot

    @slot.setter
    def slot(self, new_slot):
        self._slot = new_slot

    @property
    def quality(self) -> int:
        return self._quality

    @quality.setter
    def quality(self, new_value):
        self.set_attrib("Quality", int(new_value))

    @property
    def level_req(self) -> int:
        # this is not always available from the json character download
        return self.requires.get("Level", 0)

    @level_req.setter
    def level_req(self, new_value):
        new_value = int(new_value)
        if new_value:
            self.set_attrib("Level", int(new_value))
        else:
            self.requires.pop("Level", 0)

    @property
    def armour(self):
        # return self.attribs.get("armour", 0)
        # Stat has added / increased armour added to it. Use our calculated version.
        return self._armour

    @armour.setter
    def armour(self, new_value):
        # Stat has added / increased armour added to it. Use our calculated version.
        self._armour = int(new_value)
        # new_value = int(new_value)
        # if new_value == 0:
        #     self.attribs.pop("armour", 0)
        # else:
        #     self.attribs["armour"] = new_value

    @property
    def evasion(self):
        # return self.attribs.get("evasion", 0)
        # Stat has added / increased evasion added to it. Use our calculated version.
        return self._evasion

    @evasion.setter
    def evasion(self, new_value):
        # Stat has added / increased armour added to it. Use our calculated version.
        self._evasion = int(new_value)
        # new_value = int(new_value)
        # if new_value == 0:
        #     self.attribs.pop("evasion", "")
        # else:
        #     self.attribs["evasion"] = new_value

    @property
    def energy_shield(self):
        # return self.attribs.get("energy_shield", 0)
        # Stat has added / increased energy shield added to it. Use our calculated version.
        return self._energy_shield

    @energy_shield.setter
    def energy_shield(self, new_value):
        # Stat has added / increased armour added to it. Use our calculated version.
        self._energy_shield = int(new_value)
        # new_value = int(new_value)
        # if new_value == 0:
        #     self.attribs.pop("energy_shield", "")
        # else:
        #     self.attribs["energy_shield"] = new_value

    @property
    def shaper(self) -> bool:
        return "Shaper" in self.influences

    @property
    def elder(self) -> bool:
        return "Elder" in self.influences

    @property
    def warlord(self) -> bool:
        return "Warlord" in self.influences

    @property
    def hunter(self) -> bool:
        return "Hunter" in self.influences

    @property
    def crusader(self) -> bool:
        return "Crusader" in self.influences

    @property
    def redeemer(self) -> bool:
        return "Redeemer" in self.influences

    @property
    def exarch(self) -> bool:
        return "Exarch" in self.influences

    @property
    def eater(self) -> bool:
        return "Eater" in self.influences

    def get_attrib(self, attrib_name, default_value):
        """
        Return the value of an attribute, if it exists. elsewise return your supplied default.
        :param attrib_name: str
        :param default_value: anything
        :return: attrib's value
        """
        return self.attribs.get(attrib_name, default_value)

    def set_attrib(self, attrib_name, value):
        """
        Save an attribute, or delete it if value is 0, "", {}, [] or False
        :param attrib_name: str:
        :param value: anything
        :return: N/A
        """
        if value:
            self.attribs[attrib_name] = value
        else:
            self.attribs.pop(attrib_name, 0)

    def load_from_ggg_json(self, _json):
        """
        Load internal structures from the downloaded json
        """
        rarity_map = {0: "NORMAL", 1: "MAGIC", 2: "RARE", 3: "UNIQUE", 9: "RELIC"}

        def get_property(_json_item, _name, _default):
            """
            Get a property from a list of property tags. Not all properties appear to be mandatory.

            :param _json_item: the gem reference from the json download
            :param _name: the name of the property
            :param _default: a default value to be used if the property is not listed/found
            :return: Either the string value if found or the _default value passed in.
            """
            for _prop in _json_item:
                if _prop.get("name") == _name and _prop.get("suffix") != "(gem)":
                    value = _prop.get("values")[0][0].replace("+", "").replace("%", "")
                    return value
            return _default

        self.base_name = _json.get("typeLine", "")
        # for magic and normal items, name is blank
        self.title = _json.get("name", "")
        # self.UniqueID = _json["id"]
        self._slot = slot_map[_json["inventoryId"]]
        self.rarity = rarity_map[int(_json.get("frameType", 0))]

        # Mods
        for mod in _json.get("explicitMods", []):
            self.full_explicitMods_list.append(Mod(self.settings, mod))
        # for mod in _json.get("craftedMods", []):
        #     self.full_explicitMods_list.append(Mod(f"{{crafted}}{mod}"))
        self.explicitMods = self.full_explicitMods_list

        for mod in _json.get("enchantMods", []):
            self.implicitMods.append(Mod(self.settings, f"{{crafted}}{mod}"))
        for mod in _json.get("scourgeMods", []):
            self.implicitMods.append(Mod(self.settings, f"{{crafted}}{mod}"))
        for mod in _json.get("implicitMods", []):
            self.implicitMods.append(Mod(self.settings, mod))

        self.properties = _json.get("properties", {})
        if self.properties:
            self.quality = get_property(_json["properties"], "Quality", "0")
        self.ilevel = _json.get("ilvl", 0)
        self.corrupted = _json.get("corrupted", False)
        self.abyss_jewel = _json.get("abyssJewel", False)
        self.synthesised = _json.get("synthesised", False)
        if _json.get("fractured", False):
            self.fracturedMods = _json.get("fracturedMods", None)
        if _json.get("crucible", False):
            self.crucibleMods = _json.get("crucibleMods", None)
        if _json.get("requirements", None):
            self.level_req = int(get_property(_json["requirements"], "Level", "0"))
        # Process sockets and their grouping
        if _json.get("sockets", None) is not None:
            current_socket_group_number = -1
            socket_line = ""
            for socket in _json["sockets"]:
                this_group = socket["group"]
                if this_group == current_socket_group_number:
                    socket_line += f"-{socket['sColour']}"
                else:
                    socket_line += f" {socket['sColour']}"
                    current_socket_group_number = this_group
            # there will always be a leading space from the routine above
            self.sockets = socket_line.strip()
        """
        delve 	?bool 	always true if present
        synthesised 	?bool 	always true if present
        """
        influences = _json.get("influences", None)
        if influences is not None:
            # each entry is like 'shaper=true'
            for influence in influences:
                key = f'{influence.split("=")[0].title()} Item'
                if key in influencers:
                    self.influences.append(key)
        self.all_stats = [
            mod for mod in self.implicitMods + self.explicitMods + self.fracturedMods + self.crucibleMods if mod.line_with_range
        ]
        self.tooltip()
        # load_from_ggg_json

    def import_from_poep_json(self, _json):
        """
        Load internal structures from the downloaded json
        !!! Important note. Not everything comes through. Corrupted and Influences are two that i've noted aren't there.
        Crafts are just part of the explicits
        """
        # Example {'name': "The Poet's Pen", 'baseName': 'Carved Wand', 'uniqueName': "The Poet's Pen",
        # 'rarity': 'UNIQUE', 'quality': 20, 'baseStatRoll': 1, 'implicits': ['15% increased Spell Damage'],
        # 'explicits': ['+1 to Level of Socketed Active Skill Gems per 25 Player Levels',
        # 'Trigger a Socketed Spell when you Attack with this Weapon, with a 0.25 second Cooldown',
        # 'Adds 3 to 5 Physical Damage to Attacks with this Weapon per 3 Player Levels', '8% increased Attack Speed']}
        print(f"import_from_poep_json: {_json=}")
        self.base_name = _json.get("baseName", "")
        # for magic and normal items, name is blank
        self.title = _json.get("name", "")
        # Slot info will only be present for equipped items
        self._slot = _json.get("slot", "")
        if self._slot != "":
            self._slot = slot_map[self._slot.title()]
        self.rarity = _json.get("rarity", "")
        self.quality = _json.get("quality", "0")
        # import doesn't have socket info
        self.sockets = self.base_item.get("initial_sockets", "")
        # import doesn't have corruption info
        # import doesn't have influence info
        # import doesn't have craft info

        # Mods
        for mod in _json.get("explicits", []):
            self.full_explicitMods_list.append(Mod(self.settings, mod))
        self.explicitMods = self.full_explicitMods_list

        for mod in _json.get("enchants", []):
            self.implicitMods.append(Mod(self.settings, f"{{crafted}}{mod}"))
        for mod in _json.get("scourgeMods", []):
            self.implicitMods.append(Mod(self.settings, f"{{crafted}}{mod}"))
        for mod in _json.get("implicits", []):
            self.implicitMods.append(Mod(self.settings, mod))

        self.all_stats = [
            mod for mod in self.implicitMods + self.explicitMods + self.fracturedMods + self.crucibleMods if mod.line_with_range
        ]
        self.tooltip()
        # load_from_ggg_json

    def load_from_json(self, json, default_rarity=bad_text):
        """
        Fill variables from json dict
        :param json: dict: the loaded json dict
        :param default_rarity: str: a default rarity. Useful for the uniue and rare templates
        :return: boolean
        """

        self.pob_item = json
        if default_rarity != bad_text:
            self.rarity = default_rarity
        # print(f"item: load_from_json: {self.pob_item=}")
        self.attribs = self.pob_item["Attribs"]
        self.requires = self.pob_item["Requires"]

        # trigger building of self.name and self.type
        self.base_name = self.base_name

        # get all the variant information
        self.variants = self.pob_item.get("Variants", [])
        if self.variants:
            # Remove "current" in case it's crept in there
            # self.variants.pop("current", None)
            self.variant_names = [""]  # Variants are numbered from one, insert a blank for index 0
            self.variant_names.extend(self.variants)
            # print(f"item.load_from_json: {self.variant_names=}")
            self.alt_variants = self.pob_item.get("Alt Variants", {})

            variant_base_names = self.pob_item.get("Variant Entries", {}).get("base_name", {})
            if variant_base_names and self.current_variant > 0:
                self.base_name = variant_base_names[str(self.current_variant)]

        # get some common attribs. Less common ones can use item.get_attrib()
        self.armour = self.get_attrib("armour", 0)
        self.armour_base_percentile = float(self.get_attrib("armour_base_percentile", "0.0"))
        self.evasion = self.attribs.get("evasion", "0")
        self.evasion_base_percentile = float(self.get_attrib("evasion_base_percentile", "0.0"))
        self.energy_shield = self.attribs.get("energy_shield", "0")
        self.energy_shield_base_percentile = float(self.get_attrib("energy_shield_base_percentile", "0.0"))
        self.limited_to = self.get_attrib("Limited to", "")
        self.ilevel = self.get_attrib("item Level", 0)
        # self.level_req = self.get_attrib("Level", 0)
        self.quality = self.get_attrib("Quality", 0)
        self.radius = self.get_attrib("Radius", "")  # Threshold Jewels have radius

        # This is for crafted items, Rare templates
        self.crafted_item = self.pob_item.get("Crafted", {})

        self.influences = self.pob_item.get("Influences", {})
        # if self.pob_item.get("Fractured", {}):
        #     for mod_xml in self.pob_item["Fractured"]["Mod"]:
        #         mod = Mod(self.settings, mod_xml.text)
        #         self.fracturedMods.append(mod)
        # if self.pob_item.get("Crucible", {}):
        #     for mod_xml in self.pob_item["Crucible"]["Mod"]:
        #         mod = Mod(self.settings, mod_xml.text)
        #         self.crucibleMods.append(mod)

        # Implicits will be there, even if empty.
        for line in self.pob_item.get("Implicits", {}):
            mod = Mod(self.settings, line)
            self.full_implicitMods_list.append(mod)
            # check for variants and if it's our variant, add it to the smaller implicit mod list
            if "variant" in line:
                m = re.search(r"{variant:([\d,]+)}(.*)", line)
                if str(self.current_variant) in m.group(1).split(","):
                    self.implicitMods.append(mod)
            else:
                self.implicitMods.append(mod)

        # Explicits will be there, even if empty.
        for line in self.pob_item.get("Explicits", {}):
            mod = Mod(self.settings, line)
            self.full_explicitMods_list.append(mod)
            # check for variants and if it's our variant, add it to the smaller explicit mod list
            if self.current_variant != 0 and "variant" in line:
                v = re.search(r"{variant: ?([\d,]+)}(.*)", line)
                if str(self.current_variant) in v.group(1).split(","):
                    self.explicitMods.append(mod)
            else:
                self.explicitMods.append(mod)
            g = re.search(r"Grants Level (\d+) (.*) Skill", line)
            if g:
                self.grants_skill_level.append(int(g.group(1)))
                self.grants_skill.append(g.group(2))
        # print(f"{self.title}, {self.grants_skill}, {self.grants_skill_level}, {self.current_variant=}")

        # mod for mod in self.implicitMods + self.explicitMods + self.fracturedMods + self.crucibleMods if mod.line_with_range
        self.all_stats = [mod for mod in self.implicitMods + self.explicitMods if mod.line_with_range]
        self.rarity_colour = ColourCodes[self.rarity].value  # needed as this function does need to set self.rarity
        self.tooltip()
        return True
        # load_from_json

    # def load_from_xml_v2(self, xml, default_rarity=bad_text):
    #     """
    #     Fill variables from the version 2 xml
    #     Needed for uniques.xml
    #
    #     :param xml: the loaded xml
    #     :param default_rarity: str: a default rarity. Useful for the uniue and rare templates
    #     :return: boolean
    #     """
    #
    #     def get_variant_value(_xml, entry_name, default_value):
    #         """
    #
    #         :param _xml: ElementTree: Part of xml to load entry from
    #         :param entry_name: str: entry name for variant_entries
    #         :param default_value: str: a suitable default value for the entry being tested
    #         :return: str of the entries value or the default value, or the variant value as applicable
    #         """
    #         _entry = _xml.get(entry_name, default_value)
    #         if _entry == "variant":
    #             # check which value is our variant
    #             for _line in self.variant_entries[entry_name]:
    #                 v = re.search(r"(.*){variant:([\d,]+)}(.*)", _line)
    #                 if str(self.current_variant) in v.group(2).split(","):
    #                     return v.group(3)
    #         return _entry
    #
    #     self.pob_item = deepcopy(empty_item_dict)
    #     self.attribs = self.pob_item["Attribs"]
    #     self.requires = self.pob_item["Requires"]
    #
    #     self.id = xml.get("id", 0)
    #     self.title = xml.get("title", "")
    #     self.rarity = xml.get("rarity", default_rarity)
    #
    #     # get all the variant information
    #     variants_xml = xml.find("Variants")
    #     if variants_xml is not None:
    #         for entry in list(variants_xml):
    #             self.variant_names.append(entry.text)
    #
    #     variant_entries_xml = xml.find("VariantEntries")
    #     if variant_entries_xml is not None:
    #         for base_names_xml in variant_entries_xml.find("base_name"):
    #             print_a_xml_element(base_names_xml)
    #
    #         for idx, entry in enumerate(variant_entries_xml):
    #             self.variant_entries.setdefault(entry.tag, {})[str(idx)] = entry.text
    #
    #     variant_xml = xml.find("Variants")
    #     if variant_xml is not None:
    #         self.max_variant = int(variant_xml.get("max", "0"))
    #         self.current_variant = self.max_variant
    #         if self.max_variant == 0:
    #             self.current_variant = int(variant_xml.get("current", f"{len(self.variant_names) - 1}"))
    #         for alt in range(1, 9):
    #             value = variant_xml.get(f"alt{alt}", "")
    #             if value != "":
    #                 self.alt_variants[alt] = int(value)
    #
    #     if self.variant_entries.get("base_name", bad_text) == bad_text:
    #         self.base_name = xml.get("base_name", "")
    #     else:
    #         self.base_name = self.variant_entries["base_name"][str(self.current_variant - 1)]
    #
    #     self.sockets = xml.get("sockets", "")
    #     self.level_req = xml.get("level_req", 0)
    #     self.set_attrib("league", xml.get("league", ""))
    #     self.set_attrib("source", xml.get("source", ""))
    #     self.set_attrib("upgrade", xml.get("upgrade", ""))
    #     self.corrupted = str_to_bool(xml.get("corrupted", "False"))
    #     attribs = xml.find("Attribs")
    #     if attribs is not None:
    #         self.armour = attribs.get("armour", "0")
    #         self.armour_base_percentile = float(attribs.get("armour_base_percentile", "0.0"))
    #         self.evasion = attribs.get("evasion", "0")
    #         self.evasion_base_percentile = float(attribs.get("evasion_base_percentile", "0.0"))
    #         self.energy_shield = attribs.get("energy_shield", "0")
    #         self.energy_shield_base_percentile = float(attribs.get("energy_shield_base_percentile", "0.0"))
    #         self.limited_to = attribs.get("limited_to", "")
    #         self.ilevel = int(attribs.get("ilevel", "0"))
    #         self.level_req = int(attribs.get("level_req", "0"))
    #         self.quality = int(attribs.get("quality", "0"))
    #         self.radius = attribs.get("radius", "")
    #
    #     # This is for crafted items
    #     crafted_xml = xml.find("Crafted")
    #     if crafted_xml is not None:
    #         self.crafted_item["Prefix"] = []
    #         for prefix in crafted_xml.findall("Prefix"):
    #             self.crafted_item["Prefix"].append(prefix.text)
    #         self.crafted_item["Suffix"] = []
    #         for suffix in crafted_xml.findall("Suffix"):
    #             self.crafted_item["Suffix"].append(suffix.text)
    #
    #     influence_xml = xml.find("Influences")
    #     if influence_xml is not None:
    #         for influence in influence_xml.findall("Influence"):
    #             self.influences.append(influence.text)
    #             self.pob_item.setdefault("Influences", []).append(influence)
    #     # fracture_xml = xml.find("Fractured")
    #     # if fracture_xml is not None:
    #     #     for mod_xml in fracture_xml.findall("Mod"):
    #     #         mod = Mod(self.settings, mod_xml.text)
    #     #         self.fracturedMods.append(mod)
    #     # crucible_xml = xml.find("Crucible")
    #     # if crucible_xml is not None:
    #     #     for mod_xml in crucible_xml.findall("Mod"):
    #     #         mod = Mod(self.settings, mod_xml.text)
    #     #         self.crucibleMods.append(mod)
    #
    #     imp = xml.find("Implicits")
    #     for mod_xml in imp.findall("Mod"):
    #         line = mod_xml.text
    #         self.pob_item["Implicits"].append(line)
    #         mod = Mod(self.settings, mod_xml.text)
    #         self.full_implicitMods_list.append(mod)
    #         # check for variants and if it's our variant, add it to the smaller implicit mod list
    #         if "variant" in line:
    #             m = re.search(r"{variant:([\d,]+)}(.*)", line)
    #             if str(self.current_variant) in m.group(1).split(","):
    #                 self.implicitMods.append(mod)
    #         else:
    #             self.implicitMods.append(mod)
    #
    #     exp = xml.find("Explicits")
    #     for mod_xml in exp.findall("Mod"):
    #         line = mod_xml.text
    #         self.pob_item["Explicits"].append(line)
    #         mod = Mod(self.settings, mod_xml.text)
    #         self.full_explicitMods_list.append(mod)
    #         # check for variants and if it's our variant, add it to the smaller explicit mod list
    #         if "variant" in line:
    #             m = re.search(r"{variant: ?([\d,]+)}(.*)", line)
    #             if str(self.current_variant) in m.group(1).split(","):
    #                 self.explicitMods.append(mod)
    #         else:
    #             self.explicitMods.append(mod)
    #
    #     requires_xml = xml.find("Requires")
    #     if requires_xml is not None:
    #         for req in requires_xml:
    #             self.requires[req.tag] = req.text
    #             self.pob_item["Requires"][req.tag] = req.text
    #
    #         # mod for mod in self.implicitMods + self.explicitMods + self.fracturedMods + self.crucibleMods if mod.line_with_range
    #     self.all_stats = [mod for mod in self.implicitMods + self.explicitMods if mod.line_with_range]
    #     self.tooltip()
    #     return True
    #     # load_from_xml_v2

    def save(self):
        """"""
        # Need to work out what has changed in variables that don't directly access the json dict.
        return self.pob_item

    def find_base_stats(self):
        """
        Find base_armour, etc by removing any additions, quality or multipliers
        :return: N/A
        """
        self.all_stats = [
            mod.line_with_range for mod in self.implicitMods + self.explicitMods + self.fracturedMods + self.crucibleMods  # if mod
        ]
        if self.quality:
            if self._armour:
                self.base_armour = int(self._armour * (1 - (self.quality / 100)))
                # print(f"{self.base_armour=}")

            if self._evasion:
                # adds, multiples, more = self.get_stat(0, "Evasion", 0)
                # value = float(self._evasion) * ((100 - multiples + more + self.quality) / 100)
                # multiples = 100 + (multiples + more + self.quality)
                # self.base_evasion = int(self._evasion / multiples * 100) - adds
                self.base_evasion = int(self._evasion / (1 - (self.quality / 100)) * 100)
                # print(f"{self.base_evasion=}")

            if self._energy_shield:
                # adds, multiples, more = self.get_stat(0, "Energy Shield", 0)
                # value = float(self._energy_shield) * (1 - ((multiples + more + self.quality) / 100))
                # multiples = 100 + (multiples + more + self.quality)
                # self.base_energy_shield = int(self._energy_shield / multiples * 100) - adds
                self.base_energy_shield = int(self._energy_shield / (1 - (self.quality / 100)) * 100)
                # print(f"{self.base_energy_shield=}")
        else:
            self.base_armour = self._armour
            self.base_evasion = self._evasion
            self.base_energy_shield = self._energy_shield

    def get_stat(self, start_value, search_str, default_value=0, debug=False):
        """
        Get a simple "+nn to 'stat'" or "nn% incresed 'stat'". See examples in 'calc_stat'.
        Can't do minion stats as they look similar to regular stats
              'Minions have 10% increased maximum Life' vs '8% increased maximum Life' (they can use search_stats_list_for_regex)
        :param start_value: int / float.
        :param search_str: EG: 'Life', 'Strength'
        :param default_value: int / float: A value that suits the calculation if no stats found.
        :param debug: bool: Ease of printing facts for a given specification.
        :return: int: The updated value.
        """
        # find increases and additions. Some objects have things like '+21 to Dexterity and Intelligence', so use .* in regex.
        adds = sum(search_stats_list_for_regex(self.all_stats, rf"(?!Minions)([-+]?\d+) to .*{search_str}", default_value, debug))
        value = start_value + adds
        if debug:
            print(f"get_simple_stat: {search_str}: {value=}, {start_value=}, {adds=}")

        multiples = sum(
            search_stats_list_for_regex(self.all_stats, rf"^(?!Minions)([-+]?\d+)% increased {search_str}", default_value, debug)
        )
        multiples -= sum(
            search_stats_list_for_regex(self.all_stats, rf"^(?!Minions)([-+]?\d+)% reduced {search_str}", default_value, debug)
        )
        value += multiples / 100 * value
        if debug:
            print(f"get_simple_stat: {value=}, {multiples=}")

        more = math.prod(search_stats_list_for_regex(self.all_stats, rf"^(?!Minions)([-+]?\d+)% more {search_str}", 0, debug))
        more -= math.prod(search_stats_list_for_regex(self.all_stats, rf"^(?!Minions)([-+]?\d+)% less {search_str}", 0, debug))
        if debug:
            print(f"get_simple_stat: {value=}, {more=}, {((more  / 100 ) + 1 )=}")
        if more:
            value = ((more / 100) + 1) * int(value)
        if debug:
            print(f"get_simple_stat: {value=}")
        return adds, multiples, more

    def tooltip(self, force=False):
        """
        Create a tooltip. Hand crafted html anyone ?

        :param force: Bool. Set to true to force recalculation of TT. EG: Use for when changing variants.
        :return: str: the tooltip
        """
        if not force and self.base_tooltip_text != "":
            return
        tip = (
            f"<style>"
            f"table, th, td {{border: 1px solid {self.rarity_colour}; border-collapse: collapse;}}"
            f"td {{text-align: center;}}"
            f"</style>"
            f'<table width="425">'
            f"<tr><th>"
        )
        item_id = self.settings._pob_debug and f"#{self.id}" or ""
        tip += html_colour_text(self.rarity_colour, f"{self.name}   {item_id}")
        for influence in self.influences:
            tip += f"<br/>{html_colour_text(influence_colours[influence], influence)}"
        tip += "</th></tr>"

        # stats
        stats = ""
        if self.armour:
            stats += f"Armour: {self.armour}<br/>"
        if self.evasion:
            stats += f"Evasion Rating: {self.evasion}<br/>"
        if self.energy_shield:
            stats += f"Energy Shield: {self.energy_shield}<br/>"
        if self.sub_type:
            # print(f"{self.type}, {self.sub_type}")
            stats += f"{self.sub_type}<br/>"
        # if self.type in weapon_classes:
        #     print(f"{self.type}, {self.sub_type}")
        #     stats += f"{self.type}<br/>"
        if self.quality != 0:
            stats += f"Quality: {self.quality}%<br/>"
        if self.sockets != "":
            socket_text = ""
            for socket in self.sockets:
                if socket in "RBGAW":
                    socket_text += html_colour_text(ColourCodes[socket].value, socket)
                else:
                    socket_text += socket
            stats += f'Sockets: {socket_text.replace("-", "=")}<br/>'
        if stats:
            tip += f'<tr><td>{stats.rstrip("<br/>")}</td></tr>'

        if self.limited_to != "":
            tip += f"<tr><td>Limited to: <b>{self.limited_to}</b></td></tr>"
        reqs = ""
        if self.level_req > 0:
            reqs += f"Level <b>{self.level_req}</b>"
        if self.requires:
            for req, val in self.requires.items():
                match req:
                    case "Int" | "Dex" | "Str":
                        reqs += f', <b>{html_colour_text(req, f"{val}")} {req}</b>'
                    case "Class":
                        reqs += f", <b>Class {html_colour_text(val.upper(), val)}</b>"
                    case "Level":
                        pass  # this has been added above
                    case _:
                        reqs += f", <b>{req}</b>"
        if reqs:
            tip += f'<tr><td>Requires {reqs.lstrip(", ")}</td></tr>'
        if len(self.implicitMods) > 0:
            mods = ""
            for mod in self.implicitMods:
                mods += mod.tooltip
            tip += f'<tr><td>{mods.rstrip("<br/>")}</td></tr>'
        fractured = ""
        if len(self.fracturedMods) > 0:
            mods = ""
            for mod in self.fracturedMods:
                fractured += mod.tooltip
            # tip += f'<tr><td>{fractured.rstrip("<br/>")}</td></tr>'
        if len(self.explicitMods) > 0:
            mods = ""
            for mod in self.explicitMods:
                if not mod.corrupted:
                    mods += mod.tooltip
            tip += f'<tr><td>{fractured}{mods.rstrip("<br/>")}</td></tr>'
        if len(self.crucibleMods) > 0:
            mods = ""
            for mod in self.crucibleMods:
                mods += mod.tooltip
            tip += f'<tr><td>{mods.rstrip("<br/>")}</td></tr>'

        if self.corrupted:
            tip += f'<tr><td>{html_colour_text("STRENGTH", "Corrupted")}</td></tr>'
        tip += f"</table>"
        # self.base_tooltip_text = tip
        return tip

    def get_active_mods(self) -> None:
        """
        Account for mods that have updated the implicit values of items (like dmg, ES, armour, etc)
        Also find base stat value (EG base_armour = armour - quality) to enable quality to be edited.
        This is mainly used for calcs.
        Updates self.active_mods: dict: List of all mods that can be used for calcs
        :return: N/A
        """
        if self.active_mods:
            return

        # https://regex101.com/r/YRTdJY/1
        # Exclude stats for equipment that has innate mods (eg ES, Armour, Damage)
        debug = False
        if debug:
            print(f"{self.name}=")
        for stat in self.all_stats:
            if debug:
                print(f"{stat}")
                print("Armour", re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Armour", stat))
                print("Evasion", re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Evasion", stat))
                print("Energy Shield", re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Energy Shield", stat))
            if self._armour and re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Armour", stat):
                pass
            elif self._evasion and re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Evasion", stat):
                pass
            elif self._energy_shield and re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Energy Shield", stat):
                pass
            else:
                # self.active_mods[stat] = {"id": f"{self.id}", "name": f"{self.name}"}
                self.active_mods.append(stat)
        if debug:
            print(self.active_mods)

        if self.quality:
            # print(f"{self.name}, {self._armour}, {((100+self.quality) / 100)=}")
            qual_ratio = (100 + self.quality) / 100  # for 20% this is 1.2
            if self._armour:
                self.base_armour = round(self._armour / qual_ratio)
                # print(f"{self.base_armour=}")

            if self._evasion:
                self.base_evasion = round(self._evasion / qual_ratio)
                # print(f"{self.base_evasion=}")

            if self._energy_shield:
                self.base_energy_shield = round(self._energy_shield / qual_ratio)
                # print(f"{self.base_energy_shield=}")
        else:
            self.base_armour = self._armour
            self.base_evasion = self._evasion
            self.base_energy_shield = self._energy_shield
