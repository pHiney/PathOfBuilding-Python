"""A Player represents an in-game character at a specific progression point.

A unique Player is defined by: level, class selection, ascendancy selection,
skill selection, and itemization across the item sets.
"""

from copy import deepcopy
import math
import re

from PySide6.QtWidgets import QLabel, QSpinBox

from PoB.constants import PlayerClasses, bad_text, default_max_charges, extraSaveStats, player_stats_list
from PoB.utils import format_number, print_call_stack
from ui.PoB_Main_Window import Ui_MainWindow
from widgets.ui_utils import search_stats_list_for_regex

# 2 base accuracy per level.
# 50 life and gains additional 12 life per level.
# 40 mana and gains additional 6 mana per level.
# 15 evasion rating.
# Every 10 Strength grants
# An additional 5 maximum life
# 2% increased melee physical damage
#
# Every 10 Dexterity grants
# An additional 20 accuracy rating
# 2% increased evasion rating
#
# Every 10 Intelligence grants
# An additional 5 maximum mana
# 2% increased maximum energy shield

class_stats = {
    PlayerClasses.SCION: {"str": 20, "dex": 20, "int": 20},
    PlayerClasses.MARAUDER: {"str": 32, "dex": 14, "int": 14},
    PlayerClasses.RANGER: {"str": 14, "dex": 32, "int": 14},
    PlayerClasses.WITCH: {"str": 14, "dex": 14, "int": 32},
    PlayerClasses.DUELIST: {"str": 23, "dex": 23, "int": 14},
    PlayerClasses.TEMPLAR: {"str": 23, "dex": 14, "int": 23},
    PlayerClasses.SHADOW: {"str": 14, "dex": 23, "int": 23},
}


class Player:
    def __init__(self, settings, build, _win: Ui_MainWindow, _minion=False) -> None:
        self.minion = _minion
        self.settings = settings
        self.build = build
        self.json_build = build.json_build
        self.win = _win
        self.player_class = build.current_class
        # self.ascendancy = build.ascendancy
        self.level = build.level
        # dictionary lists of the stat elements
        self.stats = {}
        self.mainhand = {}
        self.offhand = {}
        # dictionary list of things like ManaHasCost = True
        self.conditions = {}
        # self.skills = []
        # self.item_sets = set()
        # self.minions = set()
        # self.tree = None
        self.json_player_class = None
        self.nodes = set()  # set of active Nodes()
        self.items = []
        self.item_player_stats = {}
        self.node_player_stats = {}
        self.all_player_stats = {}
        self.item_minion_stats = {}
        self.node_minion_stats = {}
        self.all_minion_stats = {}
        # List of warnings
        self.warnings = []

    def __repr__(self) -> str:
        return f"Level {self.level} {self.player_class.name}"

    def load(self, _build, minion=False):
        """
        ToDo: Should we load and keep stats - or clear them ???
        Load stats from the build object, even ones we may not be able to deal with (except table entries).
        We keep valid entries that we may not yet support so that we don't destroy another tool's ability

        :param _build: build json dict
        :param minion: bool
        :return: N/A
        """
        self.json_build = _build
        self.minion = minion
        # Strip all stats. They are only there for third party tools. We will do our own calcs and save them.
        stat_name = self.minion and "MinionStat" or "PlayerStat"
        # self.json_build[stat_name].clear()

    def save(self):
        """
        Save internal structures back to the build object

        :return: N/A
        """
        stat_name = self.minion and "MinionStat" or "PlayerStat"
        # Remove everything and then add ours
        # for stat in self.json_build[stat_name]:
        #     self.json_build.remove(stat)
        # for name in self.stats:
        #     if self.stats[name]:
        #         self.json_build.append(ET.fromstring(f'<{stat_name} stat="{name}" value="{self.stats[name]}" />'))
        # Stats that are included in the build xml but not shown on the left hand side of the PoB window.
        # for name in extraSaveStats:
        #     if self.stats.get(name, None):
        #         self.json_build.append(ET.fromstring(f'<{stat_name} stat="{name}" value="{self.stats[name]}" />'))

    # def save_to_xml(self, xml_build):
    #     """
    #     Save internal structures back to the build object
    #
    #     :param xml_build: build xml
    #     :return: N/A
    #     """
    #     stat_name = self.minion and "MinionStat" or "PlayerStat"
    #     # Remove everything and then add ours
    #     for stat in xml_build.findall(stat_name):
    #         xml_build.remove(stat)
    #     for name in self.stats:
    #         if self.stats[name]:
    #             xml_build.append(ET.fromstring(f'<{stat_name} stat="{name}" value="{self.stats[name]}" />'))
    #     # Stats that are included in the build xml but not shown on the left hand side of the PoB window.
    #     for name in extraSaveStats:
    #         if self.stats.get(name, None):
    #             xml_build.append(ET.fromstring(f'<{stat_name} stat="{name}" value="{self.stats[name]}" />'))

    def calc_stats(self, active_items, test_item=None, test_node=None):
        """
        Calculate Stats (eventually we want to pass in a new set of items, new item, new tree, etc to compare against.
        Examples:
        #id: 55373 ['+12 to maximum Life', '+5 to Strength']
        #id: 49772 ['+40 to Strength', '8% increased Strength']
        #id: 3723 [ "6% increased maximum Life", "5% increased Strength" ]
        #id: 27929 ["+20 to maximum Energy Shield", "+20 to maximum Mana", "+20 to Intelligence"]
        #id: 23989 ["+15 to all Attributes", ...]
        :param: active_items: list() of Item() for items that are currently selected
        :param: test_item: Item() - future comparison
        :param: test_node: Node() - future comparison
        :return:
        """
        # ToDo: use  re.compile()
        # print(f"Calc_Stats: {active_items=}")
        # self.stats["WithPoisonDPS"] = 123.70
        return

        self.clear()
        self.player_class = self.build.current_class
        self.json_player_class = self.build.current_tree.classes[self.player_class]
        self.items = active_items

        # Get all the nodes that have stat values
        for node_id in self.build.current_spec.nodes:
            node = self.build.current_tree.nodes.get(node_id, None)
            # print(f"{node_id=}, {node.name=}, {node.stats=}")
            if node is not None and node.stats:
                # print(node_id, node.stats)
                self.nodes.add(node)
                for stat in node.stats:
                    if "Minion" in stat:
                        self.node_minion_stats[f"{stat}::{node.id}"] = {"id": f"{node_id}", "name": f"{node.name}"}
                    else:
                        self.node_player_stats[f"{stat}::{node.id}"] = {"id": f"{node_id}", "name": f"{node.name}"}

        # Get all the Mastery nodes that have stat values
        for node_id in self.build.current_spec.masteryEffects:
            node = self.build.current_tree.nodes.get(node_id, None)
            if node:
                # print(f"{node_id=}, {node.stats=}")
                self.nodes.add(node)
                effect_id = self.build.current_spec.get_mastery_effect(node_id)
                effect = node.masteryEffects[effect_id]
                if effect:
                    stat = effect["stats"][0]
                    if "Minion" in stat:
                        self.node_minion_stats[f"{stat}::{node.id}"] = {"id": f"{node_id}", "name": f"{node.name}"}
                    else:
                        self.node_player_stats[f"{stat}::{node.id}"] = {"id": f"{node_id}", "name": f"{node.name}"}
        # print(f"{len(self.node_player_stats)=}, {self.node_player_stats=}")

        # Get stats from all active items
        # print(self.items)
        for item in self.items:
            # print(f"{item.name=}, {item.active_stats=}")
            for stat in item.active_stats:
                if "Minion" in stat:
                    self.item_minion_stats[f"{stat}::{item.id}"] = {"id": f"{item.id}", "name": f"{item.name}"}
                else:
                    self.item_player_stats[f"{stat}::{item.id}"] = {"id": f"{item.id}", "name": f"{item.name}"}

        # print(f"{len(self.item_player_stats)=}, {self.item_player_stats=}")
        self.all_player_stats.update(self.node_player_stats)
        self.all_player_stats.update(self.item_player_stats)
        self.all_minion_stats.update(self.node_minion_stats)
        self.all_minion_stats.update(self.item_minion_stats)
        # print(f"{len(self.all_player_stats)=}, {self.all_player_stats.keys()=}")
        # print(f"{len(self.all_minion_stats)=}, {self.all_minion_stats.keys()=}")

        self.calc_attribs()
        self.calc_life()
        self.calc_mana()
        self.calc_es()
        self.calc_armour()
        self.calc_evasion()
        self.calc_charges()
        self.calc_res()

    def get_simple_stat(self, start_value, search_str, spec_str="", default_value=0, debug=False, multiple_returns=False):
        """
        Get a simple "+nn to 'stat'" or "nn% increased 'stat'". See examples in 'calc_stat'.
        Can't do minion stats as they look similar to regular stats
              'Minions have 10% increased maximum Life' vs '8% increased maximum Life' (they can use search_stats_list_for_regex)
        :param start_value: int / float.
        :param search_str: EG: 'Life', 'Strength'
        :param spec_str: If set, sets the self.stats with the vlaue of increases from the tree.
        :param default_value: int / float: A value that suits the calculation if no stats found.
        :param debug: bool: Ease of printing facts for a given specification.
        :param multiple_returns: bool: Return the individual values.
        :return: int: The updated value.
        """
        # find increases and additions. Some objects have things like '+21 to Dexterity and Intelligence', so use .* in regex.
        # for resistances % will be used (+30%). Others like life, dex, armour do not.
        adds = sum(search_stats_list_for_regex(self.all_player_stats, rf"([-+]?\d+)%? to.*{search_str}", default_value, debug))
        value = start_value + adds
        if debug:
            print(f"get_simple_stat: {search_str}: {value=}, {start_value=}, {adds=}")

        node_multiples = sum(
            search_stats_list_for_regex(self.node_player_stats, rf"([-+]?\d+)% increased {search_str}", default_value, debug)
        )
        node_multiples -= sum(
            search_stats_list_for_regex(self.node_player_stats, rf"([-+]?\d+)% reduced {search_str}", default_value, debug)
        )
        if spec_str:
            self.stats[f"{spec_str}"] = node_multiples

        item_multiples = sum(
            search_stats_list_for_regex(self.item_player_stats, rf"([-+]?\d+)% increased {search_str}", default_value, debug)
        )
        item_multiples -= sum(
            search_stats_list_for_regex(self.item_player_stats, rf"([-+]?\d+)% reduced {search_str}", default_value, debug)
        )
        multiples = node_multiples + item_multiples
        value += multiples / 100 * value
        if debug:
            print(f"get_simple_stat: {value=}, {node_multiples=}, {item_multiples=}")

        more = math.prod(search_stats_list_for_regex(self.item_player_stats, rf"^([-+]?\d+)% more {search_str}", 0, debug))
        more -= math.prod(search_stats_list_for_regex(self.item_player_stats, rf"^([-+]?\d+)% less {search_str}", 0, debug))
        if debug:
            print(f"get_simple_stat: {value=}, {more=}, {((more  / 100 ) + 1 )=}")
        if more:
            value = ((more / 100) + 1) * int(value)
        if debug:
            print(f"get_simple_stat: {value=}")
            # print(f"get_simple_stat: total=, ", (start_value + adds) * (1 + node_multiples + item_multiples) * (1 + (more / 100)))
        # return value
        if multiple_returns:
            return adds, multiples, more
        else:
            return value

    def calc_attribs(self, debug=False):
        """
        Calc. Str, Dex and Int.
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        all_attribs = sum(search_stats_list_for_regex(self.all_player_stats, r"^([-+]?[\d\.]+) to all Attributes", 0, debug))
        for attrib in ("Str", "Dex", "Int"):
            # attrib = "Str"
            long_str = player_stats_list[attrib]["label"]

            # Setbase value from json
            value = self.json_player_class[f"base_{attrib.lower()}"] + all_attribs
            if debug:
                print(f"{attrib=}, {value=}, {all_attribs=}")
            self.stats[attrib] = self.get_simple_stat(value, long_str, debug=debug)

            # Find MaxReq
            required = 0
            for item in self.items:
                required = max(required, int(item.requires.get(attrib, "0")))
            self.stats[f"Req{attrib}"] = required

    def calc_life(self, debug=False):
        """
        Calc. Life. Needs Str calculated first. https://www.poewiki.net/wiki/Life
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        # Setbase value.
        life = 38 + (12 * self.build.level)
        if debug:
            print(f"calc_life, Level: {self.build.level=},  {life=}, {self.stats['Str']=}, ")
        life += self.stats["Str"] / 2
        if debug:
            print(f"calc_life, Level: {life=}, {(self.stats['Str'] / 2)}")
        self.stats["Life"] = int(self.get_simple_stat(life, "maximum Life", "Spec:LifeInc", debug=debug))

    def calc_mana(self, debug=False):
        """
        Calc. Mana. Needs Int calculated first. https://www.poewiki.net/wiki/Mana
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        # Setbase value.
        mana = 34 + (6 * self.build.level)
        if debug:
            print(f"calc_mana, Level: {self.build.level=}, {mana=}, {self.stats['Int']=}, ")
        mana += self.stats["Int"] / 2
        if debug:
            print(f"calc_mana, Stats: {mana=}, {self.stats['Int'] / 2}")
        self.stats["Mana"] = self.get_simple_stat(mana, "maximum Mana", "Spec:ManaInc", debug=debug)

    def calc_armour(self, debug=False):
        """
        Calc. Armour. Needs Int calculated first. https://www.poewiki.net/wiki/Armour
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        # Setbase value.
        armour = 0
        for item in self.items:
            armour += int(item.armour)
        if debug:
            print(f"Armour: from item attribs: {armour=}")
        adds, multiples, more = self.get_simple_stat(armour, "Armour", "Spec:ArmourInc", 0, debug, True)
        if debug:
            print(f"Armour: {adds=}, {multiples=}, {more=}, {self.stats['Int']=}, {self.stats['Int'] / 5=}")
            print(f"Armour: {armour}, {self.get_simple_stat(armour, 'Armour', 'Spec:ArmourInc', 0, debug)}")

        armour = (armour + adds) * ((multiples / 100) + 1)
        if debug:
            print(f"Armour: {armour=}, {((multiples  / 100) + 1)=}")
        if more:
            armour = ((more / 100) + 1) * int(armour)
        self.stats["Armour"] = armour

    def calc_evasion(self, debug=False):
        """
        Calc. Evasion. Needs Int calculated first. https://www.poewiki.net/wiki/Evasion
        Every class starts with 15 evasion, and gains 2% increased maximum energy shield every 10 intelligence.
        Evasion is rounded up to the nearest 5.
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        # Setbase value.
        evasion = 15
        for item in self.items:
            if debug:
                print(f"Evasion: {item.title=} attribs: {item.evasion=}")
            evasion += int(item.evasion)
        if debug:
            print(f"Evasion: from item attribs: {evasion=}")
        # We need to account for Dex's max Evasion.
        adds, multiples, more = self.get_simple_stat(evasion, "Evasion", "Spec:EvasionInc", 0, debug, True)
        if debug:
            print(f"Evasion: {adds=}, {multiples=}, {more=}, {self.stats['Dex']=}, {self.stats['Dex'] / 5=}")

        evasion = (evasion + adds) * (((multiples + int(self.stats["Dex"] / 5)) / 100) + 1)
        if debug:
            print(f"Evasion: {evasion=}, {(((multiples + (self.stats['Dex'] / 5)) / 100) + 1)=}")
        if more:
            evasion = ((more / 100) + 1) * int(evasion)
        self.stats["Evasion"] = evasion
        # Round up to nearest 5
        # self.stats["Evasion"] = math.ceil(evasion / 5.0) * 5

        return

    def calc_es(self, debug=False):
        """
        Calc. Energy Shield. Needs Int calculated first. https://www.poewiki.net/wiki/Energy_shield
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        # Setbase value.
        es = 0
        for item in self.items:
            es += int(item.energy_shield)
        if debug:
            print(f"Energy Shield: from item attribs: {es=}")
        # We need to account for Int's max ES.
        adds, multiples, more = self.get_simple_stat(es, "maximum Energy Shield", "Spec:EnergyShieldInc", 0, debug, True)
        if debug:
            print(f"ES: {adds=}, {multiples=}, {more=}, {self.stats['Int']=}, {self.stats['Int'] / 5=}")

        # Every class starts with no energy shield, and gains 2% increased maximum energy shield every 10 intelligence.
        es = (es + adds) * (((multiples + int(self.stats["Int"] / 5)) / 100) + 1)
        if debug:
            print(f"ES: {es=}, {(((multiples + (self.stats['Int'] / 5)) / 100) + 1)=}")
        if more:
            es = ((more / 100) + 1) * int(es)
        self.stats["EnergyShield"] = es

    def calc_charges(self, debug=False):
        """
        Find maximum values for all sorts of charges
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        for charge_type in ("Power", "Frenzy", "Endurance", "Siphoning", "Challenger", "Blitz"):
            extra_charges = sum(
                search_stats_list_for_regex(self.all_player_stats, rf"([-+]?\d+) to Maximum {charge_type} Charges", 0, debug)
            )
            if debug:
                print(f"calc_charges, {charge_type=}, {extra_charges=}")
            # Get extra charges (which could be negative) and set that value, or 0 if it goes negative.
            total_charges = extra_charges and max(0, extra_charges + default_max_charges) or default_max_charges
            self.stats[f"{charge_type}ChargesMax"] = total_charges
            spin_widget: QSpinBox = self.win.grpbox_Combat.findChild(QSpinBox, f"spin_Num{charge_type}Charges")
            # Only update if it's at default
            if spin_widget.value() == default_max_charges:
                spin_widget.setValue(total_charges)
            label_spin_widget: QLabel = self.win.grpbox_Combat.findChild(QLabel, f"label_Num{charge_type}Charges")
            label_spin_widget.setText(format_number(total_charges, f"# of {charge_type} Charges, if not maximum: %d", self.settings))

    def calc_res(self, debug=False):
        """
        Calc. Resistance. https://www.poewiki.net/wiki/Resistance
        Must have Endurance Charges calulated first
        :param debug: bool: Ease of printing facts for a given specification
        :return: N/A
        """
        # Setbase value.
        end_chg_res = self.win.check_EnduranceCharges.isChecked() and (self.win.spin_NumEnduranceCharges.value() * 4) or 0

        all_ele_res = end_chg_res + sum(
            search_stats_list_for_regex(self.all_player_stats, r"^([-+]?\d+)% to all Elemental Resistances", 0, debug)
        )
        max_res = 75 + sum(search_stats_list_for_regex(self.all_player_stats, r"^([-+]?\d+)% to all maximum Resistances", 0, debug))
        for res in ("Fire", "Cold", "Lightning", "Chaos"):
            if res == "Chaos":
                # to all Elemental Resistances doesn't affect chaos
                all_ele_res = 0
                end_chg_res = 0
            # Setbase value from resistance penalty dropdown
            value = self.win.combo_ResPenalty.currentData()
            if debug:
                print(f"calc_res: {res=}, {value=}, {all_ele_res=}, {end_chg_res=}, {max_res=}")
            total_res = self.get_simple_stat(value, rf"{res}.*Resistance", debug=debug) + all_ele_res
            self.stats[f"{res}Resist"] = min(total_res, max_res)
            self.stats[f"{res}ResistOverCap"] = 0
            if total_res > max_res:
                self.stats[f"{res}ResistOverCap"] = total_res - max_res
            if debug:
                print(f"calc_res: {res=}, {total_res=}, {self.stats[f'{res}Resist']=}, {self.stats[f'{res}ResistOverCap']=}")

            # # Find MaxReq
            # required = 0
            # for item in self.items:
            #     required = max(required, int(item.requires.get(attrib, "0")))
            # self.stats[f"Req{attrib}"] = required

    def clear(self):
        """Erase internal variables"""
        self.items.clear()
        self.nodes.clear()
        self.node_player_stats.clear()
        self.item_player_stats.clear()
        self.item_minion_stats.clear()
        self.node_minion_stats.clear()
        self.all_player_stats.clear()
        self.all_minion_stats.clear()
        self.stats.clear()
        self.conditions.clear()
        self.mainhand.clear()
        self.offhand.clear()

    def stat_conditions(self, stat_name, stat_value, stat, max_value=0):
        """
        Check if this stat can be shown.
        :param max_value:
        :param stat_name: str
        :param stat_value: int or float
        :param stat: dictionary from player_stats_list constant (this is deepcopied so can be altered)
        :param max_value: int
        :return:
            bool: true if stat_value is not 0
            stat: a copy of the passed in stat, altered if needed.
        """
        # print(f"stat_conditions: {stat_name=}, {stat_value=}")

        # match statement, according to research on the internet, is just one big if/then/elif.
        #   This OP shows it's gets slower the further down the list it gets: https://stackoverflow.com/questions/68476576
        # Whilst this is more unwieldy from an admin point of view, it is fast - as a dictionary is a hash table
        #   and all the entries are constants.

        # Local variable we can overwrite when needed
        _stat = deepcopy(stat)

        def averagedamage():
            nonlocal _stat
            # ToDo: what is monster explode and where do we get it.
            print(f"player.averagedamage: {stat_name=}", stat)
            print(f"player.averagedamage: ", stat["attack"])
            _stat = stat["attack"]
            return True

        def reqstr():
            ret = stat_value > self.stats["Str"]
            if ret:
                self.warnings.append("You do not meet the Strength requirement")
            return ret

        def reqdex():
            ret = stat_value > self.stats["Dex"]
            if ret:
                self.warnings.append("You do not meet the Dexterity requirement")
            return ret

        def reqint():
            ret = stat_value > self.stats["Int"]
            if ret:
                self.warnings.append("You do not meet the Intelligence requirement")
            return ret

        def reqomni():
            ret = self.stats.get("Omni", bad_text) != bad_text and stat_value > self.stats["Omni"]
            if ret:
                self.warnings.append("You do not meet the Omniscience requirement")
            return ret

        def spec_manainc():
            return self.stats["Mana"] != 0

        def spec_energyshieldinc():
            return self.stats.get("EnergyShield", 0) != 0

        def spec_evasioninc():
            return self.stats.get("Evasion", 0) != 0

        def spec_armourinc():
            return self.stats.get("Armour", 0) != 0

        def elemaximumhittaken():
            return not (
                self.stats.get("LightningMaximumHitTaken", bad_text)
                == self.stats.get("FireMaximumHitTaken", bad_text)
                == self.stats.get("ColdMaximumHitTaken", bad_text)
            )

        def spec_lifeinc():
            return stat_value > 0 and self.stats.get("Life", 0) > 1

        def lifeunreserved():
            ret = stat_value < self.stats.get("Life", 0)
            if ret:
                self.warnings.append("Your unreserved Life is below 1")
            return ret

        def liferecoverable():
            return stat_value < self.stats.get("LifeUnreserved", 0)

        def liferecovery():
            # ToDo: duplicate stats
            return stat_value < self.stats.get("LifeUnreserved", 0)

        def lifeunreservedpercent():
            return stat_value < 100

        def liferegenrecovery():
            # ToDo: duplicate stats
            # label = "Life Regen"
            return (
                self.stats.get("LifeRecovery", bad_text) != bad_text
                and self.stats["LifeRecovery"] <= 0
                and self.stats.get("LifeRegenRecovery", 0) != 0,
            )

            # # label = "Life Recovery"
            # return self.stats["LifeRecovery"] > 0 and self.stats.get("LifeRegenRecovery", 0) != 0

        def manaunreserved():
            ret = stat_value < self.stats.get("Mana", 0)
            if ret:
                self.warnings.append("Your unreserved Mana is negative")
            return ret

        def manaunreservedpercent():
            return stat_value < 100

        def manaregenrecovery():
            # ToDo: duplicate stats
            pass

        # Do Not add the (). ie: averagedamage()
        stat_funcs = {
            "AverageDamage": averagedamage,
            "ReqStr": reqstr,
            "ReqDex": reqdex,
            "ReqInt": reqint,
            "ReqOmni": reqomni,
            "Spec:ManaInc": spec_manainc,
            "Spec:EnergyShieldInc": spec_energyshieldinc,
            "Spec:EvasionInc": spec_evasioninc,
            "Spec:ArmourInc": spec_armourinc,
            "LightningMaximumHitTaken": elemaximumhittaken,
            "FireMaximumHitTaken": elemaximumhittaken,
            "ColdMaximumHitTaken": elemaximumhittaken,
            "Spec:LifeInc": spec_lifeinc,
            "LifeUnreserved": lifeunreserved,
            "LifeRecovery": liferecovery,
            "LifeRecoverable": liferecoverable,
            "LifeUnreservedPercent": lifeunreservedpercent,
            "LifeRegenRecovery": liferegenrecovery,
            "ManaUnreserved": manaunreserved,
            "ManaUnreservedPercent": manaunreservedpercent,
            "ManaRegenRecovery": manaregenrecovery,
        }

        return stat_funcs[stat_name](), _stat
        #
        # ToDo: stat = "MainHand", childStat = "Accuracy", label = "MH Accuracy", fmt = "d", condFunc = function(v,o) return o.PreciseTechnique end, warnFunc = function(v,o) return v < o.Life and "You do not have enough Accuracy for Precise Technique" end, warnColor = true
        # ToDo: stat = "OffHand", childStat = "Accuracy", label = "OH Accuracy", fmt = "d", condFunc = function(v,o) return o.PreciseTechnique end, warnFunc = function(v,o) return v < o.Life and "You do not have enough Accuracy for Precise Technique" end, warnColor = true
