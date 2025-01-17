"""
A class to encapsulate one item.
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
from PoB.utils import _debug, html_colour_text, search_stats_for_skill, print_call_stack
from widgets.ui_utils import search_stats_list_for_regex


class Item:
    def __init__(self, _settings: Settings, _base_items, _slot=None, template=False) -> None:
        """
        Initialise defaults
        :param _settings: A pointer to the settings
        :param _base_items: dict: the loaded base_items.json
        :param _slot: where this item is worn/carried.
        :param template: bool: Do Not do calculations or alter the mods.
        """
        self._slot = _slot
        # the dict from json of the all items
        self.base_items = _base_items
        self.settings = _settings
        self.template = template
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

        # This is not always available from the json character download
        self.level_req = 0

        # self.id = 0
        # self.rarity = "NORMAL"
        self.ilevel = 0
        # needs to be a string as there are entries like "Limited to: 1 Survival"
        self.limited_to = ""
        # self._quality = 0
        self.influences = []
        self.two_hand = False
        self.abyss_jewel = False
        self.synthesised = False
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
        self.active_mods = []
        self.active_stats = []
        self.slots = []
        self.qual_ratio = 1.0  # a number between 1.0 and 1.3 (for 30%)

        # Some items have a smaller number of variants than the actual variant lists. Whilst these need to be fixed, this will get around it.
        self.max_variant = 0
        # dict of lists of the variant entries (EG: base_name, influences, etc)
        self.variant_entries = {}
        # I think i need to store the variants separately, for crafting. Dict of string lists, var number is index
        self.variantMods = {}

        self._armour = 0
        self._evasion = 0
        self._energy_shield = 0
        self.evasion_base_percentile = 0.0
        self.energy_shield_base_percentile = 0.0
        self.base_armour = 0  # value without quality and +nn additions/multipliers
        self.base_evasion = 0  # value without quality and +nn additions/multipliers
        self.base_energy_shield = 0  # value without quality and +nn additions/multipliers
        self.armour_base_percentile = 0.0
        self.radius = ""
        # tooltip text for the item stats, not DPS. Prevent recalculating mostly static values every time the TT is read
        self.base_tooltip_text = ""

        # special dictionary/list for the rare template items that get imported into a build
        self.crafted_item = {"Prefix": [], "Suffix": []}
        self.alt_variants = {}

        self.rarity_colour = ""
        self.grants_skill = ()

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
            self.abyss_jewel = "abyss_jewel" in self.base_item["tags"]
            if self.type == "Jewel":
                # sub_type is used to look up the jewel's image
                if self.abyss_jewel:
                    self.sub_type = "Abyss Jewel"
                else:
                    self.sub_type = self.base_name
            # setup weapon's subType
            if self.type in weapon_classes:
                if self.sub_type != "":
                    self.weapon_sub_type = self.sub_type  # This will be something like "Thrusting"
                self.sub_type = self.type
                self.type = "Weapon"
                self.two_hand = "twohand" in self.base_item["tags"]
            else:
                armour_stats = self.base_item.get("armour", {})
                for tag in armour_stats:
                    val = armour_stats.get(tag, 0)
                    # print(f"base_name: {tag=}, {val=}")
                    match tag:
                        case "ArmourBaseMax":
                            self.base_armour = val
                            self.armour = val * self.qual_ratio
                        case "EvasionBaseMax":
                            self.base_evasion = val
                            self.evasion = val * self.qual_ratio
                        case "EnergyShieldBaseMax":
                            self.base_energy_shield = val
                            self.energy_shield = val * self.qual_ratio
                        # BlockChance, MovementPenalty

            # check for any extra requires. Just attributes for now.
            reqs = self.base_item.get("req", {})
            for tag in reqs:
                match tag:
                    case "Dex" | "Int" | "Str" | "Level":
                        val = reqs.get(tag, 0)
                        # don't overwrite a current value
                        if self.requires.get(tag, bad_text) == bad_text and val != 0:
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
        return self.pob_item.get("Corrupted", False)

    @corrupted.setter
    def corrupted(self, new_value):
        if new_value:
            self.pob_item["Corrupted"] = new_value
        else:
            self.pob_item.pop("Corrupted", False)

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
        return self.get_attrib("Quality", 0)

    @quality.setter
    def quality(self, new_value):
        self.set_attrib("Quality", int(new_value))
        self.qual_ratio = (100 + int(new_value)) / 100  # for 20% this is 1.2
        self.armour = self.base_armour * self.qual_ratio
        self.evasion = self.base_evasion * self.qual_ratio
        self.energy_shield = self.base_energy_shield * self.qual_ratio
        # BlockChance, MovementPenalty

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

    @property
    def current_variant(self) -> int:
        """variants are numbered from 0, so -1 is no selection."""
        return self.pob_item.get("Selected Variant", -1)

    @current_variant.setter
    def current_variant(self, new_value):
        """variants are numbered from 0, so -1 is no selection."""
        # print(f"current_variant: {new_value=}, {self.title=}")
        # print(f"current_variant: {self.current_variant=}, {new_value=}, {self.title=}")
        new_value = int(new_value)
        if new_value < -1 or new_value >= len(self.variants):
            self.pob_item.pop("Selected Variant", -1)
        else:
            self.pob_item["Selected Variant"] = new_value

        # Now reset mod list
        self.implicitMods.clear()
        for mod in self.full_implicitMods_list:
            # print(f"\ncvi1: {mod} {new_value=}, {mod.line_for_save=}, {mod.line=}")
            # Check for variants and if it's our variant, add it to the smaller implicit mod list
            # add it if there are no variants, too
            if new_value == -1 or mod.my_variants == [] or new_value in mod.my_variants:
                self.implicitMods.append(mod)
                if mod.grants_skill:
                    self.grants_skill = mod.grants_skill
                # print(f"cvi2: {mod.line_for_save=}, {mod.line=}")

        self.explicitMods.clear()
        for mod in self.full_explicitMods_list:
            # print(f"\ncve1: {mod=} {new_value=}, {mod.line_for_save=}, {mod.corrupted=}\n")
            # Check for variants and if it's our variant, add it to the smaller explicit mod list
            # add it if there are no variants, too
            if new_value == -1 or mod.my_variants == [] or new_value in mod.my_variants:
                self.explicitMods.append(mod)
                if mod.grants_skill:
                    self.grants_skill = mod.grants_skill
            # print(f"cve2: {mod.line_for_save=}, {mod.line=}")

        self.active_mods = [mod for mod in self.implicitMods + self.explicitMods]
        self.get_active_stats()

        # If there is a mod for Corrupted, override the "Corrupted" entry in the json
        corrupted_mod = [mod.corrupted for mod in self.active_mods if mod.original_line == "Corrupted"]
        if corrupted_mod:
            corrupted = [mod.corrupted for mod in self.active_mods if mod.corrupted]
            self.corrupted = corrupted != []

        if self.variants:
            self.alt_variants = self.pob_item.get("Alt Variants", {})

            variant_base_names = self.pob_item.get("Variant Entries", {}).get("base_name", [])
            if variant_base_names and new_value >= 0:
                self.base_name = variant_base_names[new_value]

    def get_attrib(self, attrib_name, default_value):
        """
        Return the value of an attribute, if it exists - elsewise return your supplied default.
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

    def import_from_ggg_json(self, _json):
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
        self.current_variant = -1
        # self.active_mods = [mod for mod in self.implicitMods + self.explicitMods + self.fracturedMods if mod.line]
        self.tooltip(True)
        # import_from_ggg_json

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

        self.current_variant = -1
        # self.active_mods = [mod for mod in self.implicitMods + self.explicitMods + self.fracturedMods if mod.line]
        self.tooltip(True)
        # import_from_ggg_json

    def load_from_json(self, json, default_rarity=bad_text):
        """
        Fill variables from json dict
        :param json: dict: the loaded json dict.
        :param default_rarity: str: a default rarity. Useful for the unique and rare templates.
        :return: boolean
        """

        self.pob_item = json
        if default_rarity != bad_text:
            self.rarity = default_rarity
        # print(f"item: load_from_json: {self.pob_item=}")
        self.attribs = self.pob_item["Attribs"]
        self.requires = self.pob_item["Requires"]

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

        # trigger building of self.name and self.type
        self.base_name = self.base_name

        # This is for crafted items, Rare templates
        self.crafted_item = self.pob_item.get("Crafted", {})

        self.influences = self.pob_item.get("Influences", {})
        # if self.pob_item.get("Fractured", {}):
        #     for mod_xml in self.pob_item["Fractured"]["Mod"]:
        #         mod = Mod(self.settings, mod_xml.text)
        #         self.fracturedMods.append(mod)

        # Implicits will be there, even if empty.
        for line in self.pob_item.get("Implicits", {}):
            mod = Mod(self.settings, line, self.template)
            self.full_implicitMods_list.append(mod)

        # Explicits will be there, even if empty.
        for line in self.pob_item.get("Explicits", {}):
            mod = Mod(self.settings, line, self.template)
            self.full_explicitMods_list.append(mod)
            # check for variants and if it's our variant, add it to the smaller explicit mod list
            # if self.current_variant != 0 and "variant" in line:
            #     v = re.search(r"{variant: ?([\d,]+)}(.*)", line)
            #     if str(self.current_variant) in v.group(1).split(","):
            #         self.explicitMods.append(mod)
            #         skill, level = search_stats_for_skill(line, self.title == "United in Dream")
            #         if skill:
            #             self.grants_skill = (skill, level)
            # else:
            #     self.explicitMods.append(mod)
            #     # self.grants_skill = search_stats_for_skill(line, self.title == "Craiceann's Carapace")
            #     skill, level = search_stats_for_skill(line)
            #     if skill:
            #         self.grants_skill = (skill, level)

        # get all the variant information. After creating the Mod()'s
        self.variants = self.pob_item.get("Variants", [])
        self.current_variant = self.pob_item.get("Selected Variant", -1)

        self.rarity_colour = ColourCodes[self.rarity].value  # needed as this function does need to set self.rarity
        self.tooltip(True)
        return True
        # load_from_json

    def save(self):
        """"""
        # Need to work out what has changed in variables that don't directly access the json dict.
        self.pob_item["Implicits"].clear()
        for mod in self.full_implicitMods_list:
            self.pob_item["Implicits"].append(mod.line_for_save)
        self.pob_item["Explicits"].clear()
        for mod in self.full_explicitMods_list:
            self.pob_item["Explicits"].append(mod.line_for_save)
        # print(f"save: {self.pob_item=}")
        return self.pob_item

    def find_base_stats(self):
        """
        Find base_armour, etc by removing any additions, quality or multipliers
        :return: N/A
        """
        # self.active_mods = [mod.line for mod in self.implicitMods + self.explicitMods + self.fracturedMods]  # if mod
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
        adds = sum(search_stats_list_for_regex(self.active_stats, rf"(?!Minions)([-+]?\d+) to .*{search_str}", default_value, debug))
        value = start_value + adds
        if debug:
            print(f"get_simple_stat: {search_str}: {value=}, {start_value=}, {adds=}")

        multiples = sum(
            search_stats_list_for_regex(self.active_stats, rf"^(?!Minions)([-+]?\d+)% increased {search_str}", default_value, debug)
        )
        multiples -= sum(
            search_stats_list_for_regex(self.active_stats, rf"^(?!Minions)([-+]?\d+)% reduced {search_str}", default_value, debug)
        )
        value += multiples / 100 * value
        if debug:
            print(f"get_simple_stat: {value=}, {multiples=}")

        more = math.prod(search_stats_list_for_regex(self.active_stats, rf"^(?!Minions)([-+]?\d+)% more {search_str}", 0, debug))
        more -= math.prod(search_stats_list_for_regex(self.active_stats, rf"^(?!Minions)([-+]?\d+)% less {search_str}", 0, debug))
        if debug:
            print(f"get_simple_stat: {value=}, {more=}, {((more  / 100 ) + 1 )=}")
        if more:
            value = ((more / 100) + 1) * int(value)
        if debug:
            print(f"get_simple_stat: {value=}")
        return adds, multiples, more

    def tooltip(self, force=False, nl="\n"):
        """
        Create a tooltip. Hand crafted html anyone ?

        :param force: Bool. Set to true to force recalculation of TT. EG: Use for when changing variants.
        :param nl: str. NewLine. For jewel tooltip in treeview, they need "\n". Edit: seems item's tooltip will work with \n too.
        :return: str: the tooltip.
        """
        if not force and self.base_tooltip_text != "":
            return
        tip = (
            f"<style>"
            f"table, th, td {{border: 1px solid {self.rarity_colour}; border-collapse: collapse;}}"
            f"td  {{padding-left:9px; padding-right:9px; text-align: center;}}"
            f"</style>"
            f'<table width="425">'
            f"<tr><th>"
        )
        item_id = self.settings._pob_debug and f"#{self.id}" or ""
        tip += html_colour_text(self.rarity_colour, f"{self.name}   {item_id}")
        for influence in self.influences:
            tip += f"{nl}{html_colour_text(influence_colours[influence], influence)}"
        tip += "</th></tr>"

        # stats
        stats = ""
        if self.armour:
            stats += f"Armour: {self.armour}{nl}"
        if self.evasion:
            stats += f"Evasion Rating: {self.evasion}{nl}"
        if self.energy_shield:
            stats += f"Energy Shield: {self.energy_shield}{nl}"
        # if self.sub_type:
        #     print(f"{self.type=}, {self.sub_type=}")
        #     stats += f"{self.sub_type}{nl}"
        # if self.type in weapon_classes:
        #     print(f"{self.type}, {self.sub_type}")
        #     stats += f"{self.type}{nl}"
        if self.quality != 0:
            stats += f"Quality: {self.quality}%{nl}"
        if self.sockets != "":
            socket_text = ""
            for socket in self.sockets:
                if socket in "RBGAW":
                    socket_text += html_colour_text(ColourCodes[socket].value, socket)
                else:
                    socket_text += socket
            stats += f'Sockets: {socket_text.replace("-", "=")}{nl}'
        if stats:
            tip += f'<tr><td>{stats.rstrip("{nl}")}</td></tr>'

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
                # mods += f"<nobr>{mod.tooltip}"
                mods += f"{mod.tooltip}{nl}"
            tip += f'<tr><td><pre>{mods.rstrip("{nl}")}</pre></td></tr>'
        if len(self.fracturedMods) > 0:
            mods = ""
            for mod in self.fracturedMods:
                # mods += f"<nobr>{mod.tooltip}"
                mods += f"{mod.tooltip}{nl}"
            tip += f'<tr><td><pre>{mods.rstrip("{nl}")}</pre></td></tr>'
        if len(self.explicitMods) > 0:
            mods = ""
            for mod in self.explicitMods:
                if not mod.corrupted:
                    # mods += f"<nobr>{mod.tooltip}"
                    mods += f"{mod.tooltip}{nl}"
            tip += f'<tr><td><pre>{mods.rstrip("{nl}")}</pre></td></tr>'

        if self.corrupted:
            tip += f'<tr><td>{html_colour_text("STRENGTH", "Corrupted")}</td></tr>'
        tip += f"</table>"
        # self.base_tooltip_text = tip
        return tip

    def get_active_stats(self, force=False) -> list:
        """
        Account for mods that have updated the implicit values of items (like dmg, ES, armour, etc)
        Also find base stat value (EG base_armour = armour - quality) to enable quality to be edited.
        This is mainly used for calcs.
        Updates self.active_stats: list: List of all mods that can be used for calcs
        force: bool: force the re calculation (maybe after changing variant ?)
        :return: N/A
        """
        # print(f"get_active_stats1: {self.title=}, {self.active_stats=}")
        if self.active_stats and not force:
            return self.active_stats

        # https://regex101.com/r/YRTdJY/1
        # Exclude stats for equipment that has innate mods (eg ES, Armour, Damage)
        debug = False
        if debug:
            print(f"{self.title}=")
        for mod in self.active_mods:
            if debug:
                print(f"{mod.line}")
                print("Armour", re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Armour", mod.line))
                print("Evasion", re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Evasion", mod.line))
                print("Energy Shield", re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Energy Shield", mod.line))
            if self._armour and re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Armour", mod.line):
                pass
            elif self._evasion and re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Evasion", mod.line):
                pass
            elif self._energy_shield and re.search(rf"^(?!Minions).*(to|increased|reduced|more|less).*Energy Shield", mod.line):
                pass
            else:
                # self.active_stats[stat] = {"id": f"{self.id}", "name": f"{self.name}"}
                self.active_stats.append(mod.line)
        if debug:
            print(self.active_stats)

        # if self.quality:
        #     # print(f"get_active_stats: {self.title=}, {self.quality=}, {((100+self.quality) / 100)=}")
        #     if self._armour:
        #         self.base_armour = round(self._armour / self.qual_ratio)
        #         # print(f"get_active_stats: {self.title=}, {self.base_armour=}")
        #
        #     if self._evasion:
        #         self.base_evasion = round(self._evasion / self.qual_ratio)
        #         # print(f"get_active_stats: {self.title=}, {self.base_evasion=}")
        #
        #     if self._energy_shield:
        #         self.base_energy_shield = round(self._energy_shield / self.qual_ratio)
        #         # print(f"get_active_stats: {self.title=}, {self.base_energy_shield=}")
        # else:
        #     self.base_armour = self._armour
        #     self.base_evasion = self._evasion
        #     self.base_energy_shield = self._energy_shield

        # print(f"get_active_stats2: {self.title=}, {self.active_stats=}")
        return self.active_stats
