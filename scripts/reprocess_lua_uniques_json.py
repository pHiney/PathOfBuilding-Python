import sys

"""
reprocess a version one uniques xml from lua, into v2 - suitable for pyPoB.

to get uniques_flat.xml do the following in luaPoB
    open Modules/main.lua
    paste the following 12 lines at line 26, just before the line '--[[if launch.devMode then'
        local my_itemTypes = {"amulet","axe", "belt", "body", "boots", "bow", "claw", "dagger", "fishing", "flask", "generated", "gloves", "helmet", "jewel", "mace", "new", "quiver", "race", "ring", "shield", "staff", "sword", "wand",}
        local f = io.open('uniques_flat.xml', 'w')
        f:write("<?xml version='1.0' encoding='utf-8'?>\n<Uniques>\n")
        for _, name in pairs(my_itemTypes) do
            f:write("\t<"..name..">\n")
            for _, text in pairs(data.uniques[name]) do
                f:write("\t\t<Item>Rarity: UNIQUE\n"..text:gsub(" & "," &amp; ").."\t\t</Item>\n")
            end
            f:write("\t</"..name..">\n\n")
        end
        f:write("</Uniques>\n")
        f:close()
    Save the file.
    Run luaPoB as you normally would. For now ignore the 'update available' message.
    Check you have uniques_flat.xml in your normal luaPob directory.
    In luaPoB, accept the update to remove the code in main.lua
    Move uniques_flat.xml into the <directory that you cloned pyPoB/Scripts
    Open a command prompt in that directory and activate your environment. For me that is :
        ..\\.venv.\\Scripts\\activate.bat
    Then run :
        python reprocess_lua_uniques_flat_xml.py
    You will find the new xml in <directory that you cloned pyPoB>/src/data/uniques.xml.new
    Compare it against the original (your favourite diff tool (vimdiff, Total or Free Commander) or visually check it.
    Rename uniques.xml to uniques.xml.bak
    Rename uniques.xml.new to uniques.xml
    Start pyPoB and confirm everything loads.
"""

sys.path.insert(1, "../src/")
sys.path.insert(1, "../src/PoB")

from PoB.pob_file import read_json, write_json
from PoB.pob_xml import load_item_from_xml


base_items = read_json("../src/data/base_items.json")

# Some items have a smaller number of variants than the actual variant lists. Whilst these need to be fixed, this will get around it.
max_variants = {"Precursor's Emblem": "7"}

new_uniques = {}
u_json = read_json("lua_json/uniques.json")
lua_total = 0
py_total = 0
for key in sorted(u_json.keys()):
    print(f"{key}: {len(u_json[key])}")
    lua_total += len(u_json[key])
    new_uniques[key] = []
    for v1_item in u_json[key]:
        char2013 = "\u2013"
        item = load_item_from_xml(f"Rarity: UNIQUE\n{v1_item.replace(char2013,'-')}")
        item.pop("id")
        item.pop("Rarity")
        if item["title"] in max_variants.keys():
            item["Max Variants"] = max_variants[item["title"]]
        new_uniques[key].append(item)
    py_total += len(new_uniques[key])
print(f"lua: {lua_total}, py: {py_total}")
write_json("../src/data/uniques.new.json", new_uniques)
