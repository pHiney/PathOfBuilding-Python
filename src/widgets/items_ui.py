"""
This Class manages all the elements and owns some elements of the "ITEMS" tab

Abyssal sockets are precreated and are made visble or hidden based on what is in them.
"""

from copy import deepcopy
from pathlib import Path
import enum
import re

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QListWidgetItem

from ui.PoB_Main_Window import Ui_MainWindow
from PoB.settings import Settings
from PoB.build import Build
from PoB.constants import ColourCodes, empty_item_dict, empty_itemset_dict, empty_item_slots_dict, influencers, slot_map, slot_names
from PoB.item import Item
from PoB.pob_file import read_json
from PoB.utils import _debug, html_colour_text, print_call_stack
from dialogs.craft_items_dialog import CraftItemsDlg
from dialogs.itemsets_dialog import ManageItemsetDlg
from widgets.item_slot_ui import ItemSlotUI
from dialogs.popup_dialogs import yes_no_dialog

# Classes of items that can be pasted in from in game/Trade site
import_classes = (
    "Abyss Jewels, Amulets, Belts, Body Armours, Boots, Bows, Claws, Daggers, Gloves, Helmets, "
    "Hybrid Flasks, Jewels, Life Flasks, Mana Flasks, One Hand Axes, One Hand Maces, One Hand Swords, "
    "Quivers, Rings, Rune Daggers, Sceptres, Shields, Staves, Thrusting One Hand Swords, Trinkets, "
    "Two Hand Axes, Two Hand Maces, Two Hand Swords, Utility Flasks, Wands, Warstaves"
)


class ItemsUI:
    def __init__(self, _settings: Settings, _build: Build, tree_ui, _win: Ui_MainWindow) -> None:
        """
        Items UI
        :param _settings: pointer to Settings()
        :param _build: A pointer to the currently loaded build
        :param tree_ui: TreeUI: Reference to win.tree_ui to access ... what exactly
        :param _win: pointer to MainWindow()
        """
        self.settings = _settings
        # reference to Tree UI to trigger the manage tree combo
        self.tree_ui = tree_ui
        self.build = _build
        self.win = _win
        self.tr = self.settings._app.tr

        # dictionary of Items() indexed by id. This is the same order as in the dict
        self.itemlist_by_id = {}
        self.items = None
        self.current_itemset = None
        self.itemsets = None
        self.triggers_connected = False
        self.internal_clipboard = None
        self.dlg = None  # Is a dialog active
        # Flag to stop some actions happening in triggers during loading
        self.alerting = False
        # full list of all items that grant skills
        self.grant_skills_list = []

        self.base_items = read_json(Path(self.settings._data_dir, "base_items.json"))
        self.mods = read_json(Path(self.settings._data_dir, "mods.json"))
        self.hidden_skills = _settings._hidden_skills  # a copy of the hidden_skills.json from skills_ui.

        # set the key_event - handler - self.item_list_keypressed
        self.win.list_Items.key_press_handler = self.item_list_keypressed
        self.win.list_Items.set_delegate()

        """Create the ui elements for displaying on the left side of the tab"""
        # list of abyssal ui's for ease of hiding them during itemset changes
        self.abyssal_item_slot_ui_list = []
        self.abyssal_item_slot_ui_list_by_slotname = {}
        for slotname in slot_map.values():
            self.abyssal_item_slot_ui_list_by_slotname[slotname] = list()
        self.jewel_slot_ui_list = []
        # dict of all slots
        self.item_slot_ui_list = {}
        for item_label in slot_names.values():
            self.slot_ui_create_in_layout(item_label)
        self.item_slot_ui_list["Weapon 1"].other_weapon_slot = self.item_slot_ui_list["Weapon 2"]
        self.item_slot_ui_list["Weapon 1 Swap"].other_weapon_slot = self.item_slot_ui_list["Weapon 2 Swap"]
        # Are these two needed ?
        self.item_slot_ui_list["Weapon 2"].other_weapon_slot = self.item_slot_ui_list["Weapon 1"]
        self.item_slot_ui_list["Weapon 2 Swap"].other_weapon_slot = self.item_slot_ui_list["Weapon 1 Swap"]
        for name in (
            "Weapon 1",
            "Weapon 2",
            "Weapon 1 Swap",
            "Weapon 2 Swap",
            "Body Armour",
        ):
            self.slot_ui_create_abyssal_socket(name, 6)
        for name in ("Helmet", "Gloves", "Boots"):
            self.slot_ui_create_abyssal_socket(name, 4)
        self.slot_ui_create_abyssal_socket("Belt", 2)
        self.slot_ui_hide("Weapon 1 Swap", hidden=True)
        self.slot_ui_hide("Weapon 2 Swap", hidden=True)
        # self.win.frame_SocketedJewels.setVisible(False)

        self.item_types = set()
        self.uniques_items = []
        self.load_unique_items()

        # A dictionary list of jewels that the tree_view can use for showing the correct image
        self.jewels = {}

        self.rare_template_items = []
        self.load_rare_template_items()
        # dictionary list of current items in the imported items list widget
        self.import_items_list = {}
        self.fill_import_items_list("")

        self.win.combo_ItemsImportFrom.currentTextChanged.connect(self.fill_import_items_list)
        self.win.combo_ItemsImportSlot.currentIndexChanged.connect(self.change_import_slot_combo)
        self.win.combo_ItemsImportType.currentIndexChanged.connect(self.change_import_type_combo)
        self.win.combo_ItemsImportLeague.currentTextChanged.connect(self.fill_import_items_list)
        self.win.combo_ItemsImportSource.currentTextChanged.connect(self.fill_import_items_list)
        self.win.combo_ItemsImportSearchSource.currentTextChanged.connect(self.change_import_search_widgets)
        self.win.lineedit_ItemsImportSearch.textChanged.connect(self.change_import_search_widgets)
        self.win.lineedit_ItemsSearch.textChanged.connect(self.filter_items_list)
        self.win.btn_ManageItemSet.clicked.connect(self.manage_itemset_button_clicked)
        self.win.btn_ItemsManageTree.clicked.connect(self.tree_ui.open_manage_trees)
        self.win.btn_DeleteItem.clicked.connect(self.item_list_delete_item)
        self.win.btn_DeleteAllItems.clicked.connect(self.delete_all_button_clicked)
        self.alerting = True

    def setup_ui(self):
        """Call setupUI on all UI classes that need it"""
        # Delay setting the delegate so not all 1167 rows (Jan2023) are processed multiple times during startup
        self.win.list_ImportItems.set_delegate()

    @property
    def activeItemSet(self) -> int:
        return self.items.get("activeItemSet", 0)

    @activeItemSet.setter
    def activeItemSet(self, new_set):
        self.items["activeItemSet"] = new_set

    def connect_item_triggers(self):
        """re-connect widget triggers that need to be disconnected during loading and other processing"""
        # print("connect_item_triggers", self.triggers_connected)
        # print_call_stack(idx=-4)
        if self.triggers_connected:
            # Don't re-connect
            return
        self.triggers_connected = True
        self.win.btn_WeaponSwap.clicked.connect(self.weapon_swap2)
        self.win.combo_ItemSet.currentIndexChanged.connect(self.change_itemset)
        self.win.list_ImportItems.itemDoubleClicked.connect(self.import_items_list_double_clicked)
        self.win.list_Items.currentItemChanged.connect(self.item_list_on_row_changed)
        self.win.list_Items.itemClicked.connect(self.item_list_on_row_changed)
        self.win.list_Items.itemDoubleClicked.connect(self.item_list_double_clicked)

    def disconnect_item_triggers(self):
        """disconnect widget triggers that need to be disconnected during loading and other processing"""
        # print("disconnect_item_triggers", self.triggers_connected)
        # print_call_stack(idx=-4)
        if not self.triggers_connected:
            # Don't disconnect if not connected
            return
        self.triggers_connected = False
        try:
            # During shutdown at least one of these will fail and alert on the command line
            self.win.btn_WeaponSwap.clicked.disconnect(self.weapon_swap2)
            self.win.combo_ItemSet.currentIndexChanged.disconnect(self.change_itemset)
            self.win.list_ImportItems.itemDoubleClicked.disconnect(self.import_items_list_double_clicked)
            self.win.list_Items.currentItemChanged.disconnect(self.item_list_on_row_changed)
            self.win.list_Items.itemClicked.disconnect(self.item_list_on_row_changed)
            self.win.list_Items.itemDoubleClicked.disconnect(self.item_list_double_clicked)
        except RuntimeError:
            pass

    def get_item_from_clipboard(self, data=None):
        """
        Get an item from the windows or internal clipboard

        :param data: str: the clipboard data or None. Sanity checked to be an Item Class, but not of what type
        :return: bool: success
        """
        # print("ItemsUI.get_item_from_clipboard: Ctrl-V pressed")
        if self.internal_clipboard is None:
            if data is None:
                return False
            else:
                return self.process_item_from_clipboard(data)
        else:
            print("Internal clipboard")
            self.internal_clipboard = None

    def process_item_from_clipboard(self, data):
        """
        Process the string recieved during an item paste to make it usable by the Item().load function.

        :param data: str: the text from the clipboard. It has been sanity checked and looks like an item.
        :return: bool: success
        """

        def find_line(text, return_index=False, debug=False):
            # i = [i for i, l in enumerate(lines) if text in l]
            i = [i for i, l in enumerate(lines) if re.search(rf"^{text}", l)]
            if debug:
                print(f"find_line: {text=} {i=}")
            if i and i[0] != 0:
                if debug:
                    print(f"find_line: {i[0]=}")
                if return_index:
                    return i[0]
                else:
                    return lines[i[0]]
            else:
                if return_index:
                    return 0
                else:
                    return ""

        def get_all_lines_between_delimiters(index):
            _l = []
            if index >= len(lines):
                return _l
            _line = lines[index]
            if "----" in _line:
                index += 1
            while index < len(lines) and "----" not in lines[index]:
                _l.append(lines[index])
                index += 1
            return _l

        new_item = deepcopy(empty_item_dict)
        lines = [y for y in (x.strip(" \t\r\n") for x in data.splitlines()) if y]
        # print("lines", lines)
        item_class = lines.pop(0)
        m = re.search(r"(.*): (.*)", item_class)
        if m.group(2) not in import_classes:
            print("Error: Dave, I don't know what to do with this:\nUnknown 'Item Class'\n", data)
            self.win.update_status_bar(f"Item Paste: Wrong item class -> {m.group(2)}.", 10, "RED")
            return False
        line = lines.pop(0).upper()  # should be rarity
        if "RARITY" not in line:
            print("Error: Dave, I don't know what to do with this:\nNo 'Rarity'\n", data)
            self.win.update_status_bar("Item Paste: No Rarity data.", 10, "RED")
            return False

        m = re.search(r"(.*): (.*)", line)
        new_item["Rarity"] = m.group(2)
        # next one or two lines should be name and base name of item
        names = get_all_lines_between_delimiters(0)
        if not names:
            print("Error: Dave, I don't know what to do with this:\nNo 'Name Data'\n", data)
            self.win.update_status_bar("Item Paste: No Name data", 10, "RED")
            return False
        if len(names) == 1:
            new_item["base_name"] = names[0]
        elif len(names) == 2:
            new_item["title"] = names[0]
            new_item["base_name"] = names[1]
        else:
            print("Error: Dave, I don't know what to do with this:\nNo item base and/or item title\n", data)
            self.win.update_status_bar("Item Paste: No item base and/or item title", 10, "RED")
            return False

        # ToDo: Add flasks direct to items list.
        idx = find_line("Requirements:", True)
        if idx > 0:
            reqs = get_all_lines_between_delimiters(idx + 1)
            if reqs:
                for req in reqs:
                    m = re.search(r"(.*): ([+-]?\d+)", req)
                    if m:
                        new_item["Requires"][m.group(1)] = int(m.group(2))

        for search_term in ("Talisman Tier", "Item Level", "Quality"):
            line = find_line(search_term)
            if line:
                m = re.search(r"(.*): ([+-]?\d+)", line)
                if m:
                    new_item["Attribs"][search_term] = int(m.group(2))

        for search_term in ("Sockets",):
            line = find_line(search_term)
            if line != "":
                m = re.search(r"(.*): (.*)", line)
                if m:
                    new_item["Attribs"][search_term] = m.group(2)

        # influences
        for search_term in influencers:
            line = find_line(f"{search_term}$")
            if line != "":
                new_item.setdefault("Influences", []).append(line)

        # Assume that implicits and explicits are after "Item Level:"
        # Some White items have no implicits or explicits
        idx = find_line("Item Level", True) + 2
        implicits = get_all_lines_between_delimiters(idx)
        # print(f"1. {implicits=}")
        for implicit in implicits:
            if " (enchant)" in implicit:
                implicit = f'{{crafted}}{implicit.replace(" (enchant)", "")}'
            if " (crafted)" in implicit:
                implicit = f'{{crafted}}{implicit.replace(" (crafted)", "")}'
            new_item["Implicits"].append(f'{implicit.replace(" (implicit)", "")}')

        explicits = get_all_lines_between_delimiters(idx + len(implicits) + 1)
        # print(f"2. {explicits=}")
        for explicit in explicits:
            if " (fractured)" in explicit:
                explicit = f'{{fractured}}{explicit.replace(" (fractured)", "")}'
            if " (crafted)" in explicit:
                explicit = f'{{crafted}}{explicit.replace(" (crafted)", "")}'
            new_item["Explicits"].append(f'{explicit.replace(" (enchant)", "")}')

        # if plicits:
        #     # Enchants. PoB treats them as implicit crafts
        #     print("1. plicits", plicits)
        #     implicits = ""
        #     if " (enchant)" in plicits[0]:
        #         for plicit in plicits:
        #             implicits += f'{{crafted}}{plicit.replace(" (enchant)", "")}\n'
        #             # get the next stanza
        #         idx += len(plicits) + 1
        #         plicits = get_all_lines_between_delimiters(idx)
        #     print("2. plicits", plicits)
        #     if " (implicit)" in plicits[0]:
        #         for plicit in plicits:
        #             if " (crafted)" in plicit:
        #                 plicit = f'{{crafted}}{plicit.replace(" (crafted)", "")}'
        #             implicits += f'{plicit.replace(" (implicit)", "")}\n'
        #             # get the next stanza, as these will be explicits
        #         plicits = get_all_lines_between_delimiters(idx + len(plicits) + 1)
        #     implicits_len = len([y for y in (x.strip(" \t\r\n") for x in implicits.splitlines()) if y])
        #     new_item += f"Implicits: {implicits_len}\n"
        #     if implicits_len > 0:
        #         new_item += f"{implicits}\n"
        #     # Explicits
        #     print("3. plicits", plicits)
        #     for plicit in plicits:
        #         if " (crafted)" in plicit:
        #             plicit = f'{{crafted}}{plicit.replace(" (crafted)", "")}'
        #         if " (fractured)" in plicit:
        #             plicit = f'{{fractured}}{plicit.replace(" (fractured)", "")}'
        #         new_item += f"{plicit}\n"
        # end plicits

        if find_line("Corrupted") != "":
            new_item["Corrupted"] = new_item != ""

        # print("new_item", new_item)
        dlg = CraftItemsDlg(self.settings, self.base_items, self.mods, "add", self.win)
        item = Item(self.settings, self.base_items, self.hidden_skills)
        print(f"1. {item.sockets=}")
        item.load_from_json(new_item)
        print(f"2. {item.sockets=}")
        # dlg.item is a property that triggers internal procedures. Don't set it to an empty Item and expect it to work.
        dlg.item = item
        _return = dlg.exec()
        if _return:
            self.add_item_to_itemlist_lwi(dlg.item)
            self.slot_ui_add_item(dlg.item)
        else:
            print(f"Discarded: {dlg.item.name}")
        return True

    def load_from_json(self, _items):
        """
        Load internal structures from the build object.

        :param _items: Reference to build's json_items
        :return: N/A
        """
        # print("items_ui.load_from_json", _items)
        self.disconnect_item_triggers()
        self.alerting = False
        self.items = _items
        self.clear_controls(True)
        self.win.combo_ItemSet.clear()
        # add the items to the list box
        for _item in self.items["Items"]:
            new_item = Item(self.settings, self.base_items)
            new_item.load_from_json(_item)
            self.add_item_to_itemlist_lwi(new_item)
            self.itemlist_by_id[new_item.id] = new_item
            if "Jewel" in new_item.base_name:
                self.jewels[new_item.id] = new_item

        active_set_title = "Default"
        self.itemsets = self.items["ItemSets"]
        titles = [item["title"] for item in self.itemsets]
        self.win.combo_ItemSet.addItems(titles)
        self.fill_item_slot_uis()
        self.fill_jewel_slot_uis()
        self.alerting = True
        self.connect_item_triggers()
        # Trigger showing the correct itemset
        self.win.combo_ItemSet.setCurrentIndex(self.activeItemSet)

    def load_from_ggg_json(self, json_items, delete_it_all):
        """
        Load internal structures from the GGG build json.

        :param json_items: json import of the item data
        :param delete_it_all: bool: delete all current items and itemsets
        :return: N/A
        """
        # print("items_ui.load_from_ggg_json")
        self.disconnect_item_triggers()
        self.alerting = False
        if delete_it_all:
            self.item_list_delete_all_items(False)
            self.itemset_delete_all()

        # Make a new skill set
        json_character = json_items.get("character")
        self.current_itemset = self.new_itemset(f"Imported {json_character.get('name', '')}")
        # self.itemsets = self.items["ItemSets"]
        id_base = len(self.itemlist_by_id) == 0 and 1 or max(self.itemlist_by_id.keys())
        # add the items to the list box
        for idx, text_item in enumerate(json_items["items"]):
            new_item = Item(self.settings, self.base_items)
            new_item.load_from_ggg_json(text_item)
            new_item.id = id_base + idx
            self.add_item_to_itemlist_lwi(new_item)
            self.itemlist_by_id[new_item.id] = new_item
            if "Jewel" in new_item.base_name:
                self.jewels[new_item.id] = new_item
        self.fill_item_slot_uis()
        self.win.combo_ItemSet.setCurrentIndex(0)
        self.show_itemset(0, True)
        self.alerting = True
        self.connect_item_triggers()

    def import_from_poep_json(self, json_items, itemset_name):
        """
        Load internal structures from the poeplanner.com json object.

        :param json_items: Reference to the downloaded json <equipment> tag set
        :param itemset_name: str: A potential new name for this itemset
        :return: N/A
        """
        # print("items_ui.import_from_poep_json")
        """
        Example docs/test_data/LittleXyllyBleeder_poeplanner_import.json
        format under equipment is buildItems and equippedItems. 
        equippedItems is simple EG:
            { "buildItemIndex": 0, "slot": "WEAPON" },
            { "buildItemIndex": 10, "slot": "OFFHAND" },
        buildItems is a zero indexed array of entries

        """
        self.disconnect_item_triggers()
        self.alerting = False
        self.item_list_delete_all_items(False)
        self.itemset_delete_all()
        self.current_itemset = self.new_itemset(itemset_name)

        # get the slots and add them to the main buildItems array
        for idx, text_item in enumerate(json_items["equippedItems"]):
            build_item_idx = int(text_item["buildItemIndex"])
            json_items["buildItems"][build_item_idx]["slot"] = text_item["slot"].title()
        # Find the end of the itemlist_by_id list
        id_base = len(self.itemlist_by_id) == 0 and 1 or max(self.itemlist_by_id.keys())
        # add the items to the list box
        for idx, text_item in enumerate(json_items["buildItems"]):
            # print(text_item)
            new_item = Item(self.settings, self.base_items)
            new_item.import_from_poep_json(text_item)
            new_item.id = id_base + idx
            self.add_item_to_itemlist_lwi(new_item)
            self.itemlist_by_id[new_item.id] = new_item
            if "Jewel" in new_item.base_name:
                self.jewels[new_item.id] = new_item

        self.fill_item_slot_uis()
        self.win.combo_ItemSet.setCurrentIndex(0)
        self.show_itemset(0, True)
        self.save()
        self.alerting = True
        self.connect_item_triggers()

    def save(self):
        """
        Save the *current itemset* back to a object.
        This is called by import_from_poep_json, the main SaveAs routines and change itemset, prior to showing the new set.

        :return: the json dict for Items
        """
        # if self.win.list_Items.count() > 0:
        # leave this here for a bit to pick out one item
        # self.itemlist[items[0]].save(0, true)
        # json_items = self.items["Items"]
        # for child in list(json_items):
        #     json_items.remove(child)
        # for _id in self.itemlist_by_id:
        #     json_items.append(self.itemlist_by_id[_id].save_v2())

        # As these entries do not delete if not used, remove the old entries, and add the new ones.
        # self.current_itemset["Slots"] = deepcopy(empty_item_slots_dict)
        self.items["Items"].clear()
        for _id in self.itemlist_by_id:
            self.items["Items"].append(self.itemlist_by_id[_id].save())
        self.current_itemset["Slots"].clear()
        for slot_ui_name in self.item_slot_ui_list:
            slot_ui = self.item_slot_ui_list[slot_ui_name]
            if slot_ui.current_item_id != 0:
                json_self_slot_ui = {"itemId": slot_ui.current_item_id, "itemPbURL": slot_ui.itemPbURL}
                if "Flask" in slot_ui_name:
                    json_self_slot_ui["active"] = slot_ui.active
                self.current_itemset["Slots"][slot_ui_name] = json_self_slot_ui
        self.activeItemSet = self.win.combo_ItemSet.currentIndex()
        # Renumber skillsets in case they have been moved, created or deleted.
        for idx, _set in enumerate(self.items["ItemSets"]):
            _set["id"] = idx
        return self.items

    def clear_controls(self, loading=False):
        """
        Clear certain controls on the Skills tab in preparation for reloading.

        :return: N/A
        """
        # _debug("clear_controls")
        if loading:
            self.win.list_Items.clear()
            self.itemlist_by_id.clear()
        for name in self.item_slot_ui_list:
            slot: ItemSlotUI = self.item_slot_ui_list[name]
            slot.clear()
        for slot in self.abyssal_item_slot_ui_list:
            slot.setHidden(True)
        self.win.frame_SocketedJewels.setHidden(True)
        self.win.btn_DeleteItem.setEnabled(False)

    def slot_ui_create_abyssal_socket(self, item_name, number_of_sockets):
        for idx in range(number_of_sockets, 0, -1):
            ui = self.slot_ui_create_in_layout(f"{item_name} Abyssal Socket {idx}", True, item_name)
            self.abyssal_item_slot_ui_list.insert(0, ui)
            self.abyssal_item_slot_ui_list_by_slotname[item_name].insert(0, ui)

    def slot_ui_create_in_layout(self, slot_name, hidden=False, insert_after=""):
        """
        Create an item_slot_ui with the label being slot_name and add it to
            abyssal_item_slot_ui_list_by_slotname and item_slot_ui_list

        :param slot_name: str: The labels contents
        :param hidden: bool: Alt weapons are hidden by default
        :param insert_after: str: The slot_name of the item_slot_ui to insert this item_slot_ui after
        :return: item_slot_ui:
        """
        # Abyssal sockets have the item name in front, so split it out. EG: 'Belt Abyssal Socket 1'
        if "Abyssal" in slot_name:
            socket_number = slot_name.split("Socket ")
            slot_ui = ItemSlotUI(f"Abyssal #{socket_number[1]}", self.item_changed, self.win, True)
        else:
            slot_ui = ItemSlotUI(slot_name, self.item_changed, self.win, insert_after != "")
        # Find which list we are adding these to, Items or Sockets
        layout = "Socket #" in slot_name and self.win.layout_SocketedJewels or self.win.layout_EquippedItems
        if insert_after != "":
            index = layout.indexOf(self.item_slot_ui_list[insert_after]) + 1
            layout.insertWidget(index, slot_ui)
        else:
            layout.addWidget(slot_ui)
        self.item_slot_ui_list[slot_name] = slot_ui
        slot_ui.setHidden(hidden)
        self.show_hide_jewels_frame()
        return slot_ui

    def slot_ui_remove_from_layout(self, slot_name):
        slot_ui = self.item_slot_ui_list.get(slot_name, None)
        if slot_ui is not None:
            vlayout = "Socket #" in slot_name and self.win.layout_SocketedJewels or self.win.layout_EquippedItems
            vlayout.takeAt(vlayout.indexOf(slot_ui))
            del self.item_slot_ui_list[slot_name]
        self.show_hide_jewels_frame()

    def slot_ui_hide(self, slot_name, hidden):
        """
        (un)Hide an slot item.

        :param slot_name: str: Index to item_ui_list
        :param hidden: bool: Whether to hide or not
        :return:
        """
        slot_ui = self.item_slot_ui_list.get(slot_name, None)
        if slot_ui is not None:
            slot_ui.setHidden(hidden)
            if slot_ui.current_item:
                slot_ui.current_item.active = not hidden

    def slot_ui_add_item(self, item):
        """
        Add just one item to the relevant item slot(s). Each Item() knows what slot(s) it is allowed to be in.

        :param item: Item(): the item to be added.
        :return: N/A
        """
        for slot_name in item.slots:
            match slot_name:
                case "":
                    pass
                case "AbyssJewel":
                    for slot in self.abyssal_item_slot_ui_list:
                        slot.add_item(item)
                case "Jewel":
                    # Different rules for jewels
                    pass
                case _:
                    try:
                        self.item_slot_ui_list[slot_name].add_item(item)
                    except KeyError:
                        print(f"KeyError: slot_name: '{slot_name}'")
                        pass
        self.weapon_swap2(self.win.btn_WeaponSwap.isChecked())

    def slot_ui_delete_item(self, item):
        """
        Remove just one item from the relevant item slot(s). Each Item() knows what slot(s) it is allowed to be in.

        :param item: Item(): the item to be added.
        :return: N/A
        """
        for slot_name in item.slots:
            self.item_slot_ui_list[slot_name].delete_item(item)

    def fill_item_slot_uis(self):
        """fill the left hand item combos with items"""
        for _id in self.itemlist_by_id:
            self.slot_ui_add_item(self.itemlist_by_id[_id])

    def fill_jewel_slot_uis(self):
        """fill the left hand jewel combos with items"""
        # print("fill_jewel_slot_uis", len(self.itemlist_by_id), len(self.jewel_slot_ui_list))
        if len(self.itemlist_by_id) <= 0:
            return
        # Out with the old (ItemSlotUI's) ...
        for slot_ui in self.jewel_slot_ui_list:
            slot_ui.deleteLater()
        self.jewel_slot_ui_list.clear()

        # ... in with the new.
        for idx, node_id in enumerate(self.build.current_spec.sockets, 1):
            slot_ui: ItemSlotUI = self.slot_ui_create_in_layout(f"Socket #{idx}")
            slot_ui.jewel_node_id = node_id
            self.jewel_slot_ui_list.append(slot_ui)

        # Fill all those slots with jewels. sockets={socket['@nodeId']},{socket['@itemId']}
        # ToDo: Determine if a cluster jewel is allowed in slot
        # print(f"{self.build.current_spec.sockets=}")
        for j_id in self.build.current_spec.sockets.values():
            # accommodate data errors, or people fiddling.
            try:
                item = self.itemlist_by_id[j_id]
                for slot in self.jewel_slot_ui_list:
                    slot.add_item(item)
            except KeyError:
                print(f"fill_jewel_slot_uis KeyError1:, {j_id=}, {len(self.itemlist_by_id)=}, {len(self.jewel_slot_ui_list)=}")

        # print(self.jewels)
        # print(self.build.current_spec.sockets)

        # set the default item as noted per this spec
        for slot_ui in self.jewel_slot_ui_list:
            # accomodate data errors, or people fiddling.
            j_id = 0
            try:
                j_id = self.build.current_spec.sockets[slot_ui.jewel_node_id]
                item = self.itemlist_by_id[j_id]
                slot_ui.set_default_by_item_id(j_id)
                # slot_ui.set_default_by_text(item.name)
            except KeyError:
                print(f"fill_jewel_slot_uis KeyError2:, {j_id=}, {len(self.itemlist_by_id)=}, {len(self.jewel_slot_ui_list)=}")

    def show_hide_jewels_frame(self):
        show = self.win.layout_SocketedJewels.count() > 3
        self.win.frame_SocketedJewels.setVisible(show)
        if show:
            self.win.vlayout_Items2.setStretch(0, 1)
            self.win.vlayout_Items2.setStretch(1, 2)
            self.win.vlayout_Items2.setStretch(2, 2)
            self.win.vlayout_Items2.setStretch(3, 0)
        else:
            self.win.vlayout_Items2.setStretch(0, 0)
            self.win.vlayout_Items2.setStretch(1, 3)
            self.win.vlayout_Items2.setStretch(2, 0)
            self.win.vlayout_Items2.setStretch(3, 2)

    def load_unique_items(self):
        item_leagues = set()
        u_json = read_json(Path(self.settings._data_dir, "uniques.json"))
        for key in u_json.keys():
            for _item in u_json[key]:
                new_item = Item(self.settings, self.base_items, template=True)
                new_item.load_from_json(_item, "UNIQUE")
                new_item.quality = 20
                self.uniques_items.append(new_item)
                if new_item.type:
                    self.item_types.add(new_item.type)
                    self.item_types.add(new_item.sub_type)
                if new_item.league:
                    item_leagues.update(new_item.league.split(", "))

        # Update the Import items type combo
        self.item_types = sorted(self.item_types)
        self.win.combo_ItemsImportType.clear()
        self.win.combo_ItemsImportType.addItems(self.item_types)
        self.win.combo_ItemsImportType.setItemText(0, "Any Type")
        self.win.combo_ItemsImportType.view().setMinimumWidth(self.win.combo_ItemsImportType.minimumSizeHint().width())
        self.win.combo_ItemsImportLeague.clear()
        self.win.combo_ItemsImportLeague.addItems(sorted(item_leagues))
        self.win.combo_ItemsImportLeague.setItemText(0, "Any League")
        self.win.combo_ItemsImportLeague.view().setMinimumWidth(self.win.combo_ItemsImportLeague.minimumSizeHint().width())

    def load_rare_template_items(self):
        t_json = read_json(Path(self.settings._data_dir, "rare_templates.json"))
        for _item in t_json:
            new_item = Item(self.settings, self.base_items, template=True)
            new_item.load_from_json(_item, "RARE")
            self.rare_template_items.append(new_item)

    def add_item_to_itemlist_lwi(self, _item):
        """
        Add an Item() class to the list widget and internal lists.

        :param _item: Item(). The item to be added to the list
        :return: the passed in Item() class object
        """
        # print("add_item_to_itemlist_lwi", _item.name)

        # ensure the item has a valid id. Yes, this process will leave unused numbers as items get deleted.
        if _item.id == 0:
            _id = len(self.itemlist_by_id) + 1
            while self.itemlist_by_id.get(_id, 0) != 0:
                _id += 1
            _item.id = _id
        self.itemlist_by_id[_item.id] = _item
        lwi = QListWidgetItem(html_colour_text(_item.rarity, _item.name))
        lwi.setToolTip(_item.tooltip())
        lwi.setWhatsThis(_item.name)
        lwi.setData(Qt.UserRole, _item)
        self.win.list_Items.addItem(lwi)

        return _item

    def add_item_to_importlist_lwi(self, _item, idx):
        """
        Add an Item() class to the list widget.

        :param _item: Item(). The item to be added to the list
        :param idx: int. Index of this item in self.rare_template_items or self.uniques_items
        :return: the passed in Item() class object
        """
        lwi = QListWidgetItem(html_colour_text(_item.rarity, _item.name))
        lwi.setToolTip(_item.tooltip())
        lwi.setWhatsThis(_item.name)
        self.win.list_ImportItems.addItem(lwi)
        return _item

    def item_changed(self, combo: ItemSlotUI):
        """
        Called when an item is changed. What shall we do ???
        :param combo: QComboBox: The sender.
        :return: N/A
        """
        slot_name = combo.slot_name
        item: Item = combo.current_item

        if slot_name in slot_map:
            # Show/Hide the abyssal socket slots.
            num_abyssal_sockets = 0
            if item is not None:
                num_abyssal_sockets = len(item.abyssal_sockets)
            for idx, slot_ui in enumerate(self.abyssal_item_slot_ui_list_by_slotname[slot_name]):
                slot_ui.setVisible(num_abyssal_sockets != 0 and idx < num_abyssal_sockets)

        if not self.alerting:
            return
        # Any other functionality that requires a loaded system

    @Slot()
    def weapon_swap2(self, checked):
        """
        Switch between active and alternate weapons.

        :param checked: bool: state of the btn_WeaponSwap button. Checked = True means Alt is to be shown.
        :return: N/A
        """
        self.win.btn_WeaponSwap.setText(checked and "Show Main Weapons" or "Show Alt Weapons")
        self.slot_ui_hide("Weapon 1", checked)
        self.slot_ui_hide("Weapon 2", checked)
        self.slot_ui_hide("Weapon 1 Swap", not checked)
        self.slot_ui_hide("Weapon 2 Swap", not checked)
        self.win.do_calcs()

    @Slot()
    def define_item_labels(self, item=None):
        """
        Change listItems' items to include what itemset they are in, but don't list the current subset's name.

        :return: N/A
        """
        lwis = [self.win.list_Items.item(x) for x in range(self.win.list_Items.count())]
        if self.current_itemset is None:  # pretty much can't happen
            return
        curr_itemset_name = self.current_itemset["title"]
        ids_by_itemset = {}
        for itemset in self.itemsets:
            ids_by_itemset[itemset["title"]] = set(sorted([itemset["Slots"][item]["itemId"] for item in itemset["Slots"]]))
        for lwi in lwis:
            _item: Item = lwi.data(Qt.UserRole)
            subset_names = [key for key in ids_by_itemset if key != curr_itemset_name and _item.id in ids_by_itemset[key]]
            all_subset_names = [key for key in ids_by_itemset if _item.id in ids_by_itemset[key]]
            tag = ""
            # print(f" 1 {_item.name}: {_item.two_hand}")
            if all_subset_names:
                if curr_itemset_name in all_subset_names:
                    all_subset_names.remove(curr_itemset_name)
                # print(f" 2 {_item.name}: {all_subset_names}")
                if all_subset_names:
                    # print(f" 3 {_item.name}: {all_subset_names}")
                    items_subset_names = ", ".join(f'"{w}"' for w in subset_names)
                    tag = f"\t(Used in {items_subset_names})"
            else:
                tag = "\t(Unused)"
                # tag = all_subset_names == [curr_itemset_name] and "" or "\tUnused"
            lwi.setText(f"<pre>{html_colour_text(_item.rarity, _item.name)}{html_colour_text('DARKGRAY', tag)}</pre>")

    @Slot()
    def item_list_on_row_changed(self, item):
        """Are there actions we want to take when the user selects a new item"""
        # lwi = self.win.list_Items.currentItem()
        # if lwi:
        #     print("on_row_changed", lwi.whatsThis())
        # else:
        #     print("on_row_changed", item.text())
        self.win.btn_DeleteItem.setEnabled(len(self.win.list_Items.selectedItems()) > 0)

    @Slot()
    def item_list_keypressed(self, key, ctrl_pressed, alt_pressed, shift_pressed, event):
        """
        respond to keypresses in the item_list

        :param key: the event.key()
        :param ctrl_pressed: Bool: True if Control key pressed
        :param alt_pressed: Bool: True if Alt key pressed
        :param shift_pressed: Bool: True if Shift key pressed
        :param event: The actual QT event incase more preocessing is required
        :return: N/A
        """
        # print("item_list_keypressed", key, event)
        match key:
            case Qt.Key_C:
                if ctrl_pressed:
                    print("item_list_keypressed: Ctrl-C pressed")
            case Qt.Key_V:
                if ctrl_pressed:
                    self.get_item_from_clipboard()
            case Qt.Key_E:
                if ctrl_pressed:
                    print("item_list_keypressed: Ctrl-E pressed")
            case Qt.Key_Delete:
                print("item_list_keypressed: Delete pressed")

    @Slot()
    def item_list_double_clicked(self, lwi: QListWidgetItem):
        """Actions for editing an item"""
        self.win.btn_DeleteItem.setEnabled(True)
        dlg = CraftItemsDlg(self.settings, self.base_items, self.mods, "save", self.win)
        dlg.item = lwi.data(Qt.UserRole)
        _return = dlg.exec()
        if _return:
            print(f"Saved: {dlg.item.name}")
            self.itemlist_by_id[dlg.original_item.id] = dlg.item
            lwi.setData(Qt.UserRole, dlg.item)
            lwi.setText(html_colour_text(dlg.item.rarity, dlg.item.name))
            lwi.setToolTip(dlg.item.tooltip(True))
        else:
            print(f"Discarded: {dlg.item.name}")
            self.itemlist_by_id[dlg.original_item.id] = dlg.original_item
            lwi.setData(Qt.UserRole, dlg.original_item)

    @Slot()
    def item_list_delete_item(self):
        """Delete an item from list_Items (list on the right)."""
        # print(f"item_list_delete_item: {len(self.win.list_Items.selectedItems())=}")
        # Multi-select is not enabled, so it can't have more than one. Using 'for' removes the need for an 'if item selected'
        for lwi in self.win.list_Items.selectedItems():
            _item = lwi.data(Qt.UserRole)
            if yes_no_dialog(
                self.win,
                f'{self.tr("Delete Item")}: {_item.name}',
                self.tr(" This action has no undo. Are you sure ?"),
            ):
                self.slot_ui_delete_item(_item)
                self.win.list_Items.takeItem(self.win.list_Items.row(lwi))
                self.itemlist_by_id.pop(_item.id, 0)
                del lwi  # fm doco: "Items removed from a list widget will not be managed by Qt, and will need to be deleted manually."
                del _item
        self.win.btn_DeleteItem.setDisabled(True)
        self.win.list_Items.clearSelection()

    @Slot()
    def delete_all_button_clicked(self):
        """React to btn_DeleteAll being clicked"""
        self.item_list_delete_all_items(True)

    def item_list_delete_all_items(self, prompt=True):
        """Delete all Items
        !!! Do not try to attach this directly to the button's clicked() method. !!! The first parameter from that connection is 'checked'
        and it will always be false. Our first param is 'prompt', so therefore it will always be false.
        :param prompt: boolean: If called programatically from importing a build, this should be false,
                                elsewise prompt the user to be sure.
        :return: N/A
        """
        # print(f"item_list_delete_all_items: {prompt=}")
        if not prompt or yes_no_dialog(
            self.win,
            self.tr("Delete all Items"),
            self.tr(" This action has no undo. Are you sure ?"),
        ):
            self.items["Items"].clear()
            self.clear_controls(True)

    @Slot()
    def import_items_list_double_clicked(self, item: QListWidgetItem):
        """Actions for editing an item"""
        dlg = CraftItemsDlg(self.settings, self.base_items, self.mods, "add", self.win)
        dlg.item = self.import_items_list[item.whatsThis()]
        _return = dlg.exec()
        if _return:
            self.add_item_to_itemlist_lwi(dlg.item)
            self.slot_ui_add_item(dlg.item)
        else:
            print(f"Discarded: {dlg.item.name}")

    # def set_list_items_size_hint(self):
    # Keeping it for stamps. Maybe something will need it
    #     return
    #     _list = self.win.list_Items
    #     _list.setFixedSize(
    #         min(_list.sizeHintForColumn(0) + _list.frameWidth() * 2, 600),
    #         min(_list.sizeHintForRow(0) * _list.count() + 2 * _list.frameWidth(), 890),
    #     )

    def show_itemset(self, itemset_num, initial=False):
        """
        Show the nominated Item Set

        :param itemset_num: int:
        :param initial: bool: Only set during loading
        :return:
        """
        # _debug(f"show_itemset, {_itemset}, {self.current_itemset}, {self.itemsets}")
        if 0 <= itemset_num < len(self.itemsets):
            if self.current_itemset is not None:
                self.save()
                # self.clear_controls()
            self.current_itemset = self.itemsets[itemset_num]

            for slot_ui in self.abyssal_item_slot_ui_list:
                slot_ui.setHidden(True)

            """ Process the Slot entries and set default items"""
            slots = self.current_itemset.get("Slots", {})
            if slots:
                # for _name, value in slots.items():
                for slot_name in empty_item_slots_dict.keys():
                    slot_ui: ItemSlotUI = self.item_slot_ui_list.get(slot_name, None)
                    slot = slots.get(slot_name, {})
                    if slot:
                        item_id = slot.get("itemId", -1)
                        if item_id >= 0:
                            # Clear the slot if not used
                            if item_id == 0:
                                slot_ui.clear_default_item()
                            else:
                                item = self.itemlist_by_id[item_id]
                                # slot_ui.set_default_by_text(item.name)
                                slot_ui.set_default_by_item_id(item_id)
                                slot_ui.itemPbURL = slot.get("itemPbURL", "")
                                if item.type == "Flask":
                                    slot_ui.active = slot.get("active", False)
                                if "Abyssal" in slot_name:
                                    slot_ui.setHidden(False)
                    else:
                        slot_ui.clear_default_item()

                # slots = self.current_itemset["Slots"]
                # if len(slots) > 0:
                #     for slot_xml in slots:
                #         # The regex is for a data error: 1Swap -> 1 Swap
                #         slot_name = re.sub(r"([12])Swap", "\\1 Swap", slot_xml.get("name", ""))
                #         item_id = int(slot_xml.get("itemId", "-1"))
                #         if slot_name != "" and item_id >= 0:
                #             # There are illegal entries in PoB xmls, like 'Belt Abyssal Socket 3'.
                #             # They will create a KeyError. By absorbing them, we'll remove them from the xml.
                #             try:
                #                 slot_ui: ItemSlotUI = self.item_slot_ui_list[slot_name]
                #                 # Clear the slot if not used
                #                 if item_id == 0:
                #                     slot_ui.clear_default_item()
                #                 else:
                #                     item = self.itemlist_by_id[item_id]
                #                     slot_ui.set_default_by_text(item.name)
                #                     slot_ui.itemPbURL = slot_xml.get("itemPbURL", "")
                #                     if item.type == "Flask":
                #                         slot_ui.active = str_to_bool(slot_xml.get("active", "False"))
                #                     if "Abyssal" in slot_name:
                #                         slot_ui.setHidden(False)
                #             except KeyError:
                #                 pass
            else:
                # Have a guess at what could be - used for imports
                for slot_name in self.item_slot_ui_list:
                    self.item_slot_ui_list[slot_name].set_default_item()
        self.define_item_labels()

    def new_itemset(self, itemset_name="Default"):
        """

        :param itemset_name: str: A potential new name for this itemset
        :return: XML: The new Itemset
        """
        # print("new_itemset", itemset_name, len(self.itemsets))
        new_itemset = deepcopy(empty_itemset_dict)
        new_itemset["title"] = itemset_name
        self.itemsets.append(new_itemset)
        self.win.combo_ItemSet.addItem(itemset_name, new_itemset)
        # Add slot information
        # for slot_ui_name in self.item_slot_ui_list:
        #     slot_ui = self.item_slot_ui_list[slot_ui_name]
        #     item_id = slot_ui.current_item_id
        #     slot_xml = ET.fromstring(f'<Slot name="{slot_ui_name}" itemId="0"/>')
        #     new_itemset.append(slot_xml)
        return new_itemset

    @Slot()
    def change_itemset(self, _index):
        """React to the the itemset combo being changed"""
        # _debug("change_itemset", _index)
        if 0 <= _index < len(self.itemsets):
            self.show_itemset(_index)

    def rename_itemset(self, row, new_title):
        """
        Rename a set in all locations we have it set.
        :param row: int:
        :param new_title: str:
        :return: N/A
        """
        _set = self.itemsets[row]["title"] = new_title
        self.win.combo_ItemSet.setItemText(row, new_title)

    def delete_itemset(self, itemset_num):
        """
        Delete ONE itemset. Called from Manage Itemsets Dialog.

        :param: itemset: int: the itemset's number to be removed.
        :return: N/A
        """
        # print("delete_itemset")
        if self.current_itemset == self.itemsets[itemset_num]:
            if len(self.itemsets) == 1:
                self.current_itemset = None
            else:
                self.current_itemset = self.items[itemset_num == 0 and 0 or itemset_num - 1]
        self.itemsets.pop(itemset_num)
        self.win.combo_ItemSet.removeItem(itemset_num)

    def move_itemset(self, start, destination):
        """
        Move a set entry. This is called by the Manage Itemsets Dialog.

        :param start: int: The index of the spec to be moved.
        :param destination: The index where to insert the moved spec.
        :return: N/A
        """
        # _set = self.itemsets[start]
        if start < destination:
            # need to decrement dest by one as we are going to remove start first.
            destination -= 1
        _set = self.itemsets.pop(start)
        self.itemsets.insert(destination, _set)
        # Turn off triggers whist moving the combobox to stop unnecessary updates.
        self.disconnect_item_triggers()
        curr_index = self.win.combo_ItemSet.currentIndex()
        self.win.combo_ItemSet.removeItem(start)
        self.win.combo_ItemSet.insertItem(destination, _set.get("title", "Default"), _set)
        # set the SkillSet ComboBox dropdown width.
        self.win.combo_ItemSet.view().setMinimumWidth(self.win.combo_ItemSet.minimumSizeHint().width())
        if start == curr_index:
            self.win.combo_ItemSet.setCurrentIndex(destination)
        self.connect_item_triggers()

    def copy_itemset(self, index, new_name):
        """
        Copy a set and return the new copy. This is called by the Manage Itemsets Dialog.

        :param index: the row the current set is on.
        :param new_name: str: the new set's name
        :return: xml.etree.ElementTree: The new set
        """
        new_set = deepcopy(self.itemsets[index])
        index += 1
        new_set["title"] = new_name
        self.itemsets.insert(index, new_set)
        self.disconnect_item_triggers()
        self.win.combo_ItemSet.insertItem(index, new_name, new_set)
        self.connect_item_triggers()
        return new_set

    def itemset_delete_all(self):
        """Delete ALL itemsets. Called from Import functions. No user actions are attached to this"""
        # print("itemset_delete_all")
        self.current_itemset = None
        self.itemsets.clear()
        # self.win.combo_ItemSet.clear()
        self.win.combo_ItemSet.clear()

    def itemset_list_active_items(self):
        """
        Return a list() of Item() for items that are currently selected in the left
        :return: list:
        """
        # print("itemset_list_active_items")
        results = [i for i in self.itemlist_by_id.values() if i.active]
        # for item in results:
        #     print(item.name)
        self.grant_skills_list = [item.grants_skill for item in results if item.grants_skill]
        # print(f"{self.grant_skills_list=}")
        return results

    @Slot()
    def manage_itemset_button_clicked(self):
        """
        and we need a dialog ...
        :return: N/A
        """
        # Ctrl-M (from MainWindow) won't know if there is another window open, so stop opening another instance.
        if self.dlg is None:
            self.dlg = ManageItemsetDlg(self.settings, self, self.win)
            self.dlg.exec()
            self.dlg = None

    @Slot()
    def filter_items_list(self, search_text):
        """
        filter the items list widget
        :param search_text:
        :return:
        """
        # print(f"filter_items_list: {search_text}")
        self.win.list_Items.clear()
        if search_text == "":
            # Searching complete, put it all back
            for _id in self.itemlist_by_id:
                self.add_item_to_itemlist_lwi(self.itemlist_by_id[_id])
        else:
            # search item's name, type and mods.
            for _id in self.itemlist_by_id:
                item = self.itemlist_by_id[_id]
                # mod_list is just long string to search in (includes variants)
                # mod_list = " ".join(mod.line.lower() for mod in item.full_implicitMods_list)
                # mod_list += "".join(mod.line.lower() for mod in item.full_explicitMods_list)
                # if search_text in item.name.lower() or search_text in mod_list or search_text in item.type:
                if search_text in item.name.lower() or search_text in item.type or search_text in item.tooltip():
                    self.add_item_to_itemlist_lwi(item)

    @Slot()
    def fill_import_items_list(self, text):
        """
        Fill the import items list widget based on the various accompaning comboBoxes.
        Start with a list of items and trim the list, rather than adding and causing duplicates.

        :param: text: str: Not used
        :return: N/A
        """

        class ImportFromType(enum.IntEnum):
            uniques = 0
            rares = 1

        # items = []
        # self.win.list_ImportItems.clear()
        # import_from = ImportFromType(self.win.combo_ItemsImportFrom.currentIndex())
        # import_slot = self.win.combo_ItemsImportSlot.currentText()
        # match import_from:
        #     case ImportFromType.uniques:
        #         items = self.uniques_items
        #         self.win.combo_ItemsImportSort.setHidden(False)
        #         self.win.combo_ItemsImportLeague.setHidden(False)
        #         self.win.combo_ItemsImportRequirements.setHidden(False)
        #         self.win.combo_ItemsImportSource.setHidden(False)
        #     case ImportFromType.rares:
        #         items = self.rare_template_items
        #         self.win.combo_ItemsImportSort.setHidden(True)
        #         self.win.combo_ItemsImportLeague.setHidden(True)
        #         self.win.combo_ItemsImportRequirements.setHidden(True)
        #         self.win.combo_ItemsImportSource.setHidden(True)

        items = []
        self.win.list_ImportItems.clear()
        import_from = ImportFromType(self.win.combo_ItemsImportFrom.currentIndex())
        match import_from:
            case ImportFromType.uniques:
                items = self.uniques_items
                self.win.combo_ItemsImportSort.setHidden(False)
                self.win.combo_ItemsImportLeague.setHidden(False)
                self.win.combo_ItemsImportRequirements.setHidden(False)
                self.win.combo_ItemsImportSource.setHidden(False)
            case ImportFromType.rares:
                items = self.rare_template_items
                self.win.combo_ItemsImportSort.setHidden(True)
                self.win.combo_ItemsImportLeague.setHidden(True)
                self.win.combo_ItemsImportRequirements.setHidden(True)
                self.win.combo_ItemsImportSource.setHidden(True)

        # Create a new item list by appending qualifying items to a temporary list, and then resetting our item list
        # start trimming the list by league and (sub)type
        import_league = self.win.combo_ItemsImportLeague.currentText()
        import_type = self.win.combo_ItemsImportType.currentText()
        import_slot = self.win.combo_ItemsImportSlot.currentText()
        temp_list = []
        for item in items:
            if (
                ("Any" in import_type or import_type == item.sub_type)
                and ("Any" in import_league or import_league in item.league)
                and ("Any Slot" in import_slot or import_slot in item.slots)
            ):
                temp_list.append(item)
        items = temp_list

        # search item's name and mods. Only iterate through items once so as to avoid duplicates.
        search_text = self.win.lineedit_ItemsImportSearch.text().lower()
        if search_text != "":
            temp_list = []
            # mod_list = []
            for item in items:
                # mod_list is just a long string to search in (includes variants)
                mod_list = " ".join(mod.line.lower() for mod in item.full_implicitMods_list)
                mod_list += "".join(mod.line.lower() for mod in item.full_explicitMods_list)
                match self.win.combo_ItemsImportSearchSource.currentText():
                    case "Anywhere":
                        if search_text in item.name.lower() or search_text in mod_list:
                            temp_list.append(item)
                    case "Names":
                        if search_text in item.name.lower():
                            temp_list.append(item)
                    case "Modifiers":
                        if search_text in mod_list:
                            temp_list.append(item)
            items = temp_list

        if self.win.combo_ItemsImportSource.currentIndex() != 0:
            temp_list = []
            for item in items:
                source = item.source.lower()
                match self.win.combo_ItemsImportSource.currentText():
                    case "Obtainable":
                        if source != "no longer obtainable":
                            temp_list.append(item)
                    case "Unobtainable":
                        if source == "no longer obtainable":
                            temp_list.append(item)
                    case "Vendor Recipe":
                        temp_list.append(item)
                    case "Upgraded":
                        if "upgraded from" in source:
                            temp_list.append(item)
                    case "Boss Item":
                        if "drops from unique" in source:
                            temp_list.append(item)
                    case "Corruption":
                        if "vaal orb" in source:
                            temp_list.append(item)
            items = temp_list

        # ToDo: Need to know where to get level and str and stuff from the build. how to represent it in the character
        # if self.win.combo_ItemsImportRequirements.currentIndex() != 0:
        #     temp_list = []
        #     items = temp_list

        # add the culled list to the list widget and internal list
        for idx, item in enumerate(items):
            self.add_item_to_importlist_lwi(item, idx)
            self.import_items_list[item.name] = item

        if import_from == ImportFromType.uniques:
            match self.win.combo_ItemsImportSort.currentText():
                case "Sort by Name":
                    # self.win.list_ImportItems.sortItems()
                    self.win.list_ImportItems.sortItems()
        else:
            # self.win.list_ImportItems.sortItems()
            self.win.list_ImportItems.sortItems()

    @Slot()
    def change_import_slot_combo(self, index):
        """
        slot and type are mutually exclusive.
        Set type combo back to "Any Type" to prevent stupidity.

        :param index: int: Index of the combo
        :return:
        """
        if index < 0:
            return
        if index > 0:
            self.win.combo_ItemsImportType.setCurrentIndex(0)
        self.fill_import_items_list("")

    @Slot()
    def change_import_type_combo(self, index):
        """
        type and slot are mutually exclusive.
        Set slot combo back to "Any Slot" to prevent stupidity.

        :param index: int: Index of the combo
        :return:
        """
        if index < 0:
            return
        if index > 0:
            self.win.combo_ItemsImportSlot.setCurrentIndex(0)
        self.fill_import_items_list("")

    @Slot()
    def change_import_search_widgets(self, text):
        self.fill_import_items_list("")
