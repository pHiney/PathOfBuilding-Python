"""
Reprocess base_items.json into a smaller file with only relevant items
base_items.json and mods.json come from https://github.com/brather1ng/RePoE/tree/master/RePoE/data
    and are not included in the git repo

"""

import re
import sys

sys.path.insert(1, "../src/")
sys.path.insert(1, "../src/PoB")

from PoB.constants import weapon_classes
from PoB.pob_file import read_json, write_json

wanted_item_types = (
    "Amulet",
    "Belt",
    "Body Armour",
    "Boots",
    "Bow",
    "Claw",
    "Dagger",
    "Flask",
    "Gloves",
    "Helmet",
    "Jewel",
    "One Handed Axe",
    "One Handed Mace",
    "One Handed Sword",
    "Quiver",
    "Ring",
    "Sceptre",
    "Shield",
    "Staff",
    "Tincture",
    "Two Handed Axe",
    "Two Handed Mace",
    "Two Handed Sword",
    "Wand",
)

# The dictionary we will build
base_items = {}
# The dictionary of the incoming json
base_items_json = read_json("lua_json/item_bases.json")

for item_id in base_items_json:
    item = base_items_json[item_id]
    item_type = item["type"]
    if item_type not in wanted_item_types:
        print(f"Skipping {item_id}: {item_type=}")
        continue

    # create an initial set of socket colours, as no socket can be blank
    socket_number = item.get("socketLimit", 0)
    if socket_number == 0:
        # Check implicits for "Has nn Socket(s)"
        s = re.search(r"Has (\d+) Sockets?", item.get("implicit", ""))
        if s:
            max_num_sockets = int(s.group(1))
            item["initial_sockets"] = "-".join("W" * max_num_sockets)
            item["max_num_sockets"] = max_num_sockets
    else:
        item["max_num_sockets"] = socket_number
        item.pop("socketLimit", 0)
        reqs = {}
        tags = [tag for tag in item.get("req", {}) if tag in ("dex", "int", "str")]
        for tag in tags:
            new_tag = tag.replace("dex", "G").replace("int", "B").replace("str", "R")
            reqs[new_tag] = item["req"][tag]
        if reqs:
            initial_sockets = ""
            l_r = len(reqs)
            tags = list(reqs.keys())
            for idx in range(socket_number):
                initial_sockets += f"{tags[idx % l_r]}"
            if initial_sockets:
                item["initial_sockets"] = "-".join([char for char in initial_sockets])
        else:
            # No requirements, just supply some defaults
            initial_sockets = "RGBRGB"
            item["initial_sockets"] = "-".join([char for char in initial_sockets[:socket_number]])

    # Capitalise req's keys to match the program's Requires
    new_reqs = {}
    old_reqs = item.get("req", {})
    if old_reqs:
        for req, value in old_reqs.items():
            new_reqs[req.title()] = value
    item["req"] = new_reqs  # always overwrite. empty req's in original files are list(). This makes them dict in all circumstances.

    item_tags = [tag for tag in item.get("tags", {}).keys() if tag != "default"]
    if item_tags:
        item["tags"] = item_tags

    # Add item to our dictionary
    # Fix Data Inconsistency. Display the umlaut. Will there be others ?
    base_items[item_id.replace("Maelstrom", "Maelstr\u00f6m")] = item

write_json("base_items_new.json", base_items)
write_json("../src/data/base_items.new.json", base_items)
