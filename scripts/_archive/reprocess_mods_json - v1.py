"""
Reprocess base_items.json into a smaller file with only relevant items
base_items.json and mods.json come from https://github.com/brather1ng/RePoE/tree/master/RePoE/data
    and are not included in the git repo

"""
from pathlib import Path
import json


def read_json(filename):
    """
    Reads a json file
    :param filename: Name of xml to be read
    :returns: A dictionary of the contents of the file
    """
    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r") as json_file:
                _dict = json.load(json_file)
                return _dict
        except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
            print(f"Unable to open {_fn}")
    return None


def write_json(filename, _dict):
    """
    Write a json file
    :param filename: Name of json to be written
    :param _dict: New contents of the file
    :returns: N/A
    """
    _fn = Path(filename)
    try:
        with _fn.open("w") as json_file:
            json.dump(_dict, json_file, indent=4)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        print(f"Unable to write to {_fn}")


# The dictionary we will build
new_mods = {}
# The dictionary of the incoming json
mods_json = read_json("mods.json")
stat_names_json = read_json("stat_translations.json")
# dictionary lookup for stat names
stat_names = {}

for stat in stat_names_json:
    # print(type(stat), stat)
    # print(type(stat), stat["English"])
    ids = stat["ids"]
    # if len(ids) > 1:
    # continue
    print(f'\n ids:{len(ids)}, #English: {len(stat["English"])}', stat["English"])
    # print("\n", ids)
    for _id_idx in range(len(ids)):
        _id = stat["ids"][_id_idx]
        stat_names[_id] = []
        for _stat_idx in range(len(stat["English"])):
            # stat_names[_id] = []
            new_stat = {
                "name": stat["English"][_stat_idx]["string"],
                "format": stat["English"][_stat_idx]["format"],
                "condition": stat["English"][_stat_idx]["condition"],
                "index_handlers": stat["English"][_stat_idx]["index_handlers"],
            }
            # print(_id, _stat_idx)
            # print(_id,  stat["English"][_stat_idx]["condition"])
            stat_names[_id].append(new_stat)
            print(stat_names[_id])

    # else:
    #     _id = stat["ids"][0]
    #     # print(_id,  stat["English"][0]["index_handlers"])
    #     stat_names[_id] = {}
    #     stat_names[_id]["name"] = stat["English"][0]["string"]
    #     stat_names[_id]["format"] = stat["English"][0]["format"]
    #     stat_names[_id]["condition"] = stat["English"][0]["condition"]
    #     stat_names[_id]["index_handlers"] = stat["English"][0]["index_handlers"]
    #     # print(stat_names[_id])
# for item_id in mods_json:
#     print(item_id)
#     print(stat_names_json[item_id])
