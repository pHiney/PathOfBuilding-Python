"""
Reprocess base_gems.json into a smaller file with only relevant items
base_gems.json and mods.json come from https://github.com/brather1ng/RePoE/tree/master/RePoE/data
    and are not included in the git repo

"""

from pathlib import Path
import json
import sys

sys.path.insert(1, "../src/")
sys.path.insert(1, "../src/PoB")

from PoB.pob_file import read_xml, read_json, write_json


# reindex the Skill types to be a list addressed by [number], for ease of lookup.
skill_types = ["0"]
SkillType_json = read_json("lua_json/SkillType.json")
# Resort by the numeric value. Add the key into a list.
for key in sorted(SkillType_json.items(), key=lambda x: (x[1], x[0])):
    skill_types.append(key[0])
write_json("../src/data/skill_type.json", skill_types, 1)

# The dictionary we will build
base_gems = {}
# The list of dictionaries of the incoming json
base_gems_json = read_json("lua_json/lua_gems.json")
# change the key name to variantID rather than the longer Metadata/Items/Gems/SkillGemQuickstep
for gem_dict in base_gems_json:
    # print(type(gem_dict), gem_dict.keys())
    for gem_id, gem in gem_dict.items():
        base_gems[gem["variantId"]] = gem

for gem_id, gem in base_gems.items():
    # gem = base_gems[gem_id]
    name = gem["name"]

    granted_effect = gem["grantedEffect"]
    secondary = gem.get("secondaryGrantedEffect", None)

    gem["colour"] = granted_effect["color"]  # Secondary granted_effect colour is always the same as the primary.
    gem["tags"] = ",".join(sorted([tag for tag in gem["tags"].keys() if tag not in ("grants_active_skill", "support")]))
    # Don't alter tagString as it appears on the tooltip
    gem["skillId"] = gem["gameId"]

    support = granted_effect.get("support", False)
    gem["support"] = support
    if not support:
        granted_effect["skillTypes"] = sorted([int(_type) for _type in granted_effect["skillTypes"].keys()])
        if granted_effect.get("minionSkillTypes"):
            granted_effect["minionSkillTypes"] = sorted([int(_type) for _type in granted_effect["minionSkillTypes"].keys()])
        granted_effect["baseFlags"] = sorted(granted_effect["baseFlags"])

    # Delete some repeated/redundant information.
    granted_effect.pop("id", None)
    granted_effect.pop("baseTypeName", None)
    granted_effect.pop("color", None)
    granted_effect.pop("support", None)

    # Names may not match between primary and secondary, so don't delete them.
    if secondary:
        secondary.pop("color", None)
        secondary.pop("id", None)
        secondary.pop("baseTypeName", None)
        if secondary.get("skillTypes", None):
            secondary["skillTypes"] = sorted([int(_type) for _type in secondary["skillTypes"].keys()])

    # This works better than a list of things to delete, not sure why
    gem.pop("id", None)
    gem.pop("gameId", None)
    gem.pop("name", None)
    gem.pop("baseTypeName", None)

    # Only keep some tags if they are not default
    for tag in ("reqDex", "reqInt", "reqStr"):
        if gem[tag] == 0:
            del gem[tag]
    if gem["naturalMaxLevel"] == 20:
        del gem["naturalMaxLevel"]

write_json("../src/data/base_gems.json", dict(sorted(base_gems.items())), 1)

# List of dictionaries
hidden_json = read_json("lua_json/hiddenSkills.json")
hidden_skills = {}
for _dict in hidden_json:
    # print(type(_dict), _dict)
    for _id, _value in _dict.items():
        # print(f'{_id=}, {type(_value.get("skillTypes", None))=}')
        if type(_value.get("skillTypes", None)) is dict:
            _value["skillTypes"] = sorted([int(_type) for _type in _value["skillTypes"].keys()])
        if type(_value.get("minionSkillTypes", None)) is dict:
            _value["minionSkillTypes"] = sorted([int(_type) for _type in _value["minionSkillTypes"].keys()])
        _value["colour"] = _value.get("color",0)
        _value.pop("color", None)
        hidden_skills[_value["id"]] = _value
write_json("../src/data/hidden_skills.json", dict(sorted(hidden_skills.items())), 1)

# copy costs, using stat as key for easy lookup
costs_json = read_json("lua_json/costs.json")
costs = {}
for _dict in costs_json:
    # print(type(_dict), _dict)
    costs[_dict["Stat"]] = _value
write_json("../src/data/costs.json", dict(sorted(costs.items())), 1)

