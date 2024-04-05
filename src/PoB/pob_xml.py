from pathlib import Path, WindowsPath
from copy import deepcopy
import re
import traceback
import xml
import xml.etree.ElementTree as ET
import xmltodict

from PoB.constants import (
    _VERSION_str,
    bad_text,
    colourEscapes,
    default_view_mode,
    empty_build,
    empty_item_dict,
    empty_item_slots_dict,
    influencers,
    starting_scion_node,
)

from PoB.pob_file import read_xml_as_dict
from PoB.utils import _debug, bool_to_str, html_colour_text, index_exists, str_to_bool

""" ################################################### XML ################################################### """

default_spec_xml = f"""<Spec title="Default" classId="0" ascendClassId="0" masteryEffects="" nodes="{starting_scion_node}" 
treeVersion="{_VERSION_str}"></Spec>"""
default_skill_set_xml = """<SkillSet id="1" title="Default">
  <Skill mainActiveSkillCalcs="1" includeInFullDPS="false" label="" enabled="true" slot="" mainActiveSkill="1"></Skill>
</SkillSet>"""

empty_socket_group_xml = """<Skill mainActiveSkillCalcs="1" includeInFullDPS="false" label=""
enabled="true" slot="" mainActiveSkill="1"/>"""

empty_gem_xml = """<Gem enableGlobal2="false" level="1" enableGlobal1="true" skillId="" qualityId="Default" 
enabled="true" quality="0" count="1" nameSpec=""/>"""

empty_build_xml = f"""
<PathOfBuilding>
    <Build level="1" targetVersion="3_0" bandit="None" className="Scion" ascendClassName="None"
     mainSocketGroup="1" viewMode="{default_view_mode}" pantheonMajorGod="None" pantheonMinorGod="None">
            <PlayerStat stat="AverageHit" value="0"/>
     </Build>
    <Import/>
    <Calcs/>
    <Skills sortGemsByDPSField="CombinedDPS" matchGemLevelToCharacterLevel="false" activeSkillSet="1" 
        sortGemsByDPS="true" defaultGemQuality="0" defaultGemLevel="normalMaximum" showSupportGemTypes="ALL" 
        showAltQualityGems="true">
        {default_skill_set_xml}
    </Skills>
    <Items activeItemSet="1">
        <ItemSet useSecondWeaponSet="false" id="1"/>
    </Items>
    <Tree activeSpec="1">
        {default_spec_xml}
    </Tree>
    <Notes/>
    <NotesHTML/>
    <TreeView searchStr="" zoomY="0" showHeatMap="nil" zoomLevel="3" showStatDifferences="true" zoomX="0"/>
    <Config>
        <Input name="resistancePenalty" number="-60"/>
        <Input name="pantheonMinorGod" string="None"/>
        <Input name="enemyIsBoss" string="None"/>
        <Input name="pantheonMajorGod" string="None"/>
        <Input name="bandit" string="None"/>
    </Config>
</PathOfBuilding>"""


def print_a_xml_element(the_element):
    """
    Debug: Print the contents so you can see what happened and why 'it' isn't working.
    Prints the parent caller to help track when there are many of them.
    :param the_element: xml element
    :return: N/A
    """
    if the_element is None:
        print(the_element)
        return
    lines = traceback.format_stack()
    print(lines[-2].strip())
    print(ET.tostring(the_element, encoding="utf8").decode("utf8"))
    print()


def read_xml(filename):
    """
    Reads a XML file
    :param filename: Name of xml to be read
    :returns: A xml tree of the contents of the file
    """

    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r") as xml_file:
                tree = ET.parse(xml_file)
                return tree
        # parent of IOError, OSError *and* WindowsError where available
        except (EnvironmentError, FileNotFoundError, ET.ParseError):
            print(f"Unable to open {_fn}")
    return None


def write_xml(filename, _tree):
    """
    Write a XML file
    :param filename: Name of xml to be written
    :param _tree: New contents of the file as a xml tree
    :returns: N/A
    """
    _fn = Path(filename)
    try:
        with _fn.open("wb") as xml_file:
            ET.indent(_tree, "\t")
            _tree.write(xml_file, encoding="utf-8", xml_declaration=True)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        print(f"Unable to write to {_fn}")


def read_v1_custom_mods(filename):
    """
    Read the v1 xml customMods. These are linefeed separated and the linefeed will be lost when read from XML as a dict.
    Reread the file as an ET.xml and get the custom mods.
    :param filename: Name of xml to be read
    :return: str: with \n encoded in it.
    """
    custom_mods = []
    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r") as xml_file:
                string = xml_file.read()
                # Sometimes the customMods' string element end in a newline. add .? to account for this
                m = re.findall(r'<Input (.*?)".?/>', string, re.DOTALL | re.MULTILINE | re.IGNORECASE)
                if m:
                    inputs = [element for element in m if "customMods" in element]
                    # 'inputs' will be a list of one line or an empty list
                    if inputs:
                        # EG:
                        #   ['name="customMods" string="+1 to Maximum Endurance Charges\n+14% increased maximum Life\n']
                        # Get rid of unwanted bits
                        return inputs[0].replace('string="', "").replace('name="customMods"', "").strip()

        except (EnvironmentError, FileNotFoundError, ET.ParseError):
            print(f"Unable to open {_fn}")
    return ""


def write_v1_custom_mods(filename):
    """
    Read the v1 xml customMods and remove the ~^ and replace it with a newline.
    These are linefeed separated and the linefeed(s) was lost when read from XML as a dict.
    Reread the file as an text file and get the custom mods.
    :param filename: Name of xml to be read
    :return: str: with \n encoded in it.
    """
    custom_mods = []
    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r") as xml_file:
                string = xml_file.read()
            with _fn.open("w") as xml_file:
                xml_file.write(string.replace("~^", "\n"))
        except (EnvironmentError, FileNotFoundError, ET.ParseError):
            print(f"Unable to open {_fn}")
    return ""


def write_xml_from_dict(filename, _dict):
    """
    Write a XML file
    :param filename: Name of xml to be written
    :param _dict: New contents of the file
    :returns: N/A
    """
    _fn = Path(filename)
    try:
        with _fn.open("w") as xml_file:
            xml_content = xmltodict.unparse(_dict, pretty=True)
            xml_file.write(xml_content)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        print(f"Unable to write to {_fn}")


def remove_lua_colours(text):
    """
    Remove ^7 like colours
    :param text: str: string to check
    :return: str: changed string
    """
    # remove all obvious duplicate colours (mainly ^7^7)
    for idx in range(10):  # 0..9
        while f"^{idx}^{idx}" in text:
            text = text.replace(f"^{idx}^{idx}", f"^{idx}")
    # remove single charactor colours for their full versions
    for idx in range(10):
        try:
            colour_idx = text.index(f"^{idx}")
            text = html_colour_text(colourEscapes[idx].value, text[colour_idx + 2])
        except ValueError:
            pass
    return text


def load_item_from_xml(items_free_text, _id=0, debug_lines=False):
    """
    Load internal structures from the free text version of item's xml

    :param items_free_text: str: contents of the item's xml
    :param _id: int: id of the item for builds, 0 for uniques import
    :param debug_lines: Temporary to debug the process
    :return: boolean
    """

    # Entries in the item Free text
    strings = (
        "Armour",
        "Energy Shield",
        "Evasion",
        "League",
        "Limited to",
        "Radius",
        "Sockets",
        "Source",
        "Talisman Tier",
        "Unique ID",
        "Upgrade",
    )
    integers = ("Item Level", "Quality")
    floats = ("ArmourBasePercentile", "EnergyShieldBasePercentile", "EvasionBasePercentile")

    def get_attribute(n):
        """
        Get "tag: value" lines out of the current line. Only the regex result is passed in and used.
        This is a separate function as sometimes there are tag:values entries in the middle of the explicit mods.
        :param n: regex result. n.group(1) is the tag before the colon, and n.group(1) is the text after the colon.
        :return: N/A
        """
        tag = n.group(1)
        match tag:
            case tag if tag in strings:
                json_item["Attribs"][tag] = n.group(2)
            case tag if tag in integers:
                json_item["Attribs"][tag] = int(n.group(2))
            case tag if tag in floats:
                json_item["Attribs"][tag] = float(n.group(2))
            # case m.group(1) if m.group(1) in bools:
            #     json_item[m.group(1)] = str_to_bool(m.group(2))

            case "LevelReq":
                json_item["Requires"]["Level"] = int(n.group(2))
            case "Variant":
                json_item["Variants"].append(n.group(2))
            case "Selected Variant":
                """variants are numbered from 1, so 0 is no selection. !!! don't add -1"""
                json_item["Selected Variant"] = int(n.group(2))
            case "Prefix" | "Suffix":
                json_item["Crafted"][tag].append(n.group(2))
            case "Has Alt Variant":
                json_item["Alt Variants"][1] = True
            case "Selected Alt Variant":
                json_item["Alt Variants"][1] = int(n.group(2))
            case "Has Alt Variant Two":
                json_item["Alt Variants"][2] = True
            case "Selected Alt Variant Two":
                json_item["Alt Variants"][2] = int(n.group(2))
            case "Has Alt Variant Three":
                json_item["Alt Variants"][3] = True
            case "Selected Alt Variant Three":
                json_item["Alt Variants"][3] = int(n.group(2))
            case "Has Alt Variant Four":
                json_item["Alt Variants"][4] = True
            case "Selected Alt Variant Four":
                json_item["Alt Variants"][4] = int(n.group(2))
            case "Has Alt Variant Five":
                json_item["Alt Variants"][5] = True
            case "Selected Alt Variant Five":
                json_item["Alt Variants"][5] = int(n.group(2))
            case "Requires":
                _m = re.search(r"Requires: (.*)", line)
                for req in _m.group(1).split(","):
                    req = req.lower().strip()
                    if "level" in req.lower():
                        # some entries have 'Level: ' and others 'Level '
                        _r = re.search(r"(\w+):? (\d+)", f"{req}")
                        json_item["Requires"]["Level"] = int(_r.group(2))
                    elif "class" in req.lower():
                        _r = re.search(r"(\w+) (\w+)", f"{req}")
                        json_item["Requires"]["Class"] = _r.group(2)
                    else:
                        # Str nnn, etc
                        _r = re.search(r"(\d+) (\w+)", f"{req}")
                        json_item["Requires"][_r.group(2)] = int(_r.group(1))

    # Deep copy or else we end up editing the constant
    json_item = deepcopy(empty_item_dict)

    # debug_lines = True
    if debug_lines:
        print(f"{items_free_text=}")
    json_item["id"] = _id
    if "Alt Variant" in items_free_text:
        json_item["Alt Variants"] = {}
    if "Variant:" in items_free_text:
        json_item["Variants"] = []
    if "Crafted:" in items_free_text:
        json_item["Crafted"] = {"Prefix": [], "Suffix": []}

    # split lines into a list, removing any blank lines, leading & trailing spaces.
    #   stolen from https://stackoverflow.com/questions/7630273/convert-multiline-into-list
    # No colon for Requires, so add one.
    lines = [y for y in (x.strip(" \t\r\n") for x in items_free_text.replace("Requires ", "Requires: ").splitlines()) if y]
    # The first line has to be rarity !!!!
    line = lines.pop(0).strip()
    if "rarity" not in line.lower():
        _debug(f"Error: Dave, I don't know what to do with this:\n{line=}", items_free_text)
        return False
    m = re.search(r"(.*): (.*)", line)
    json_item["Rarity"] = m.group(2).upper()
    # The 2nd line is either the title or the name of a magic/normal item. This is why Rarity is first.
    line = lines.pop(0)
    if json_item["Rarity"] in ("NORMAL", "MAGIC"):
        json_item["base_name"] = line
    else:
        json_item["title"] = line
        line = lines.pop(0)
        # if "{variant" not in line:
        #     json_item["base_name"] = line
        if "{variant" in line:
            while "{variant" in line:
                v = re.search(r"{variant:([\d,]+)}(.*)", line)
                _variant_numbers = v.group(1).split(",")
                # _variant_numbers is always a list (of str), even if it contains one entry.
                for _var in _variant_numbers:
                    json_item.setdefault("Variant Entries", {}).setdefault("base_name", {})[int(_var)] = v.group(2)
                # if "{variant" in lines[0]:
                line = lines.pop(0)
            json_item["base_name"] = "variant"
        else:
            json_item["base_name"] = line

    if debug_lines:
        print("a", len(lines), lines)

    # Check for no Implicits: 0
    if "Implicits: " not in items_free_text:
        idx = 0
        while idx < len(lines) and re.search(r"(.*): ?(.*)?", lines[idx]):
            idx += 1
        lines.insert(idx, "Implicits: 0")

    """ So the first three lines/Entries are gone, so it's game on. They can come in almost any order """
    # lets get all the colon(:) separated variables first and remove them from the lines list
    # stop when we get to implicits, or the end (eg: Tabula Rasa)
    line_idx, implicits_idx, explicits_idx = (0, -1, -1)
    # We can't use enumerate as we are changing the list as we move through.
    while index_exists(lines, line_idx):
        if debug_lines:
            print("while", len(lines), lines)
        line = lines[line_idx]
        m = re.search(r"(.*): ?(.*)?", line)
        # If no : then try to identify line. Skip if we can't deal with it.
        if m is None:
            if debug_lines:
                print("m is None", line)
            if lines[line_idx] in influencers:
                json_item.setdefault("Influences", []).append(line)
                lines.pop(line_idx)
            else:
                # skip this line
                line_idx += 1
        else:
            lines.pop(line_idx)
            if m.group(1) == "Implicits":
                # implicits, if any
                for idx in range(int(m.group(2))):
                    line = lines.pop(line_idx)
                    if debug_lines:
                        print("I", len(lines), lines)
                    json_item["Implicits"].append(line)
                explicits_idx = line_idx
                break
            else:
                get_attribute(m)

    if debug_lines:
        print(f"b, {explicits_idx=}, {len(lines)=}, lines")
    # every thing that is left, from explicits_idx, is explicits ... and some other stuff
    # explicits_idx may not be zero. In some version of luaPoB, the type "eg: Tornado Wand" would appear twice.
    while len(lines) > explicits_idx:
        line = lines.pop(explicits_idx)
        # Corrupted is not a mod, but will get caught in explicits due to crap data design.
        # Some items have things like UniqueID in the middle of this too.
        if line == "Corrupted":
            json_item["Corrupted"] = True
        else:
            m = re.search(r"(.*): ?(.*)?", line)
            if m and not m.group(1).startswith("{"):
                get_attribute(m)
            else:
                json_item["Explicits"].append(line)

    if debug_lines:
        print("c", len(lines), lines)

    for line in lines:
        # do something else
        match line:
            case _:
                print(f"Item().load_from_xml: Skipped: {line} (from {json_item['title'], json_item['base_name']})")

    if debug_lines:
        print("end", len(lines), lines)
        print()

    if json_item["base_name"] == "Unset Ring" and json_item["Attribs"].get("sockets", "") == "" and "Has 1 Socket" in items_free_text:
        json_item["Attribs"]["sockets"] = "W"

    # print(f"{json_item=}")
    return json_item
    # load_item_from_xml


def load_from_xml(filename_or_xml):
    """
    Convert a lua PoB xml to a dict.
    lua PoB won't put a single Gem, Item, Spec, etc in a list. It will just appear as a single dict()
    So there are lots of checks for this and adding a single entry into a list().
    lua PoB is 1 based in it's counting, pyPob is 0 based
    :param filename_or_xml: str|dict: either a filepath for loading an xml or an ET from the iport dialog
    :return: dict
    """

    def get_param_value(_the_value, _default):
        """
        Get a parameter's value, guarding against 'nil'. These have always been see in params inside a xml element
          and only numbers or booleans. - EG: <build "secondaryAscendClassId": "nil" /> .
        So this only has to be used for param names begining with '@'.
        :param _the_value: str: The value that has been retrieved.
        :param _default: str: str version of default
        :return:
        """
        if _the_value == "" or "nil" in _the_value:
            return _default
        else:
            return _the_value

    def get_input_values(_src, _dst):
        """
        Get a list of {"@name": "key", "@string: "value"} and add it to the destination dictionary

        :param _src: list
        :param _dst: dict
        :return:
        """
        if _src and _dst is not None:
            if type(_src) is dict:
                _src = [_src]
            for _dict in _src:
                _name = _dict.pop("@name")
                _value = ""
                try:
                    key = [key for key in _dict.keys()][0]
                    match key:
                        case "@string":
                            _value = _dict[key]
                            if _name == "customMods":
                                # EG:
                                #   ['name="customMods" string="+1 to Maximum Endurance Charges\n+14% increased maximum Life\n']
                                _value = read_v1_custom_mods(filename_or_xml).replace("\n", "~^")
                        case "@boolean":
                            _value = str_to_bool(_dict[key])
                        case "@number":
                            _value = int(_dict[key])
                    _dst[_name] = _value
                except KeyError:
                    continue

    # ToDo: Complete
    if type(filename_or_xml) is xml.etree.ElementTree.ElementTree:
        xml_PoB = xmltodict.parse(ET.tostring(filename_or_xml.getroot(), encoding="utf8").decode("utf8"))
    else:
        xml_PoB = read_xml_as_dict(filename_or_xml)
    if xml_PoB is None:
        return None
    new_build = deepcopy(empty_build)
    xml_PoB = xml_PoB["PathOfBuilding"]
    json_PoB = new_build["PathOfBuilding"]

    """Build"""
    xml_build = xml_PoB["Build"]
    json_build = {
        "level": int(xml_build.get("@level", "1")),
        "targetVersion": xml_build.get("@targetVersion", "3_0"),
        "className": xml_build.get("@className", "Scion"),
        "ascendClassName": xml_build.get("@ascendClassName", "Scion"),
        "characterLevelAutoMode": str_to_bool(xml_build.get("@characterLevelAutoMode", "False")),
        "mainSocketGroup": int(xml_build.get("@mainSocketGroup", "1")) - 1,
        "viewMode": xml_build.get("@viewMode", default_view_mode),
        "PlayerStat": {},
        "MinionStat": {},
    }
    for stat_type in ("PlayerStat", "MinionStat"):
        stats = xml_build.get(stat_type, [])
        if type(stats) is dict:  # list or dict if only one
            stats = [stats]
        for stat in stats:
            name = stat.get("@stat", "")
            if name:
                try:
                    value = stat.get("@value", "")
                    if "." in value:
                        json_build[stat_type][name] = float(stat.get("@value", "0.0"))
                    else:
                        json_build[stat_type][name] = int(stat.get("@value", "0"))
                except ValueError:
                    # ValueError: invalid literal for int() with base 10: 'table: 0x1dc9d650'
                    pass
    timeless_data = xml_build.get("TimelessData", {})
    if timeless_data:
        json_build["TimelessData"] = {
            "devotionVariant1": int(timeless_data.get("@devotionVariant1", "1")),
            "devotionVariant2": int(timeless_data.get("@devotionVariant2", "1")),
            "searchListFallback": timeless_data.get("@searchListFallback", ""),
            "searchList": timeless_data.get("@searchList", ""),
            "socketFilterDistance": int(timeless_data.get("@socketFilterDistance", "0")),
        }
    json_PoB["Build"] = json_build

    """Import"""
    xml_import = xml_PoB["Import"]
    if xml_import is not None:
        json_PoB["Import"] = {
            "exportParty": str_to_bool(xml_import.get("@lastAccountHash", "false")),
            "lastAccountHash": xml_import.get("@lastAccountHash", ""),
            "lastCharacterHash": xml_import.get("@lastCharacterHash", ""),
            "lastRealm": xml_import.get("@lastRealm", ""),
            "lastLeague": xml_import.get("@lastLeague", ""),
        }

    """Calcs"""
    xml_calcs = xml_PoB["Calcs"]
    get_input_values(xml_calcs["Input"], json_PoB["Calcs"]["Input"])
    for section in xml_calcs["Section"]:
        json_PoB["Calcs"]["Sections"][section["@subsection"]] = {"collapsed": str_to_bool(section["@collapsed"]), "id": section["@id"]}

    """Notes"""
    json_PoB["Notes"] = xml_PoB["Notes"]

    """Config"""
    xml_config = xml_PoB["Config"]
    get_input_values(xml_config.get("Input", []), json_PoB["Config"]["Input"])
    get_input_values(xml_config.get("Placeholder", []), json_PoB["Config"]["Placeholder"])

    """TreeView"""
    xml_tree_view = xml_PoB["TreeView"]
    json_PoB["TreeView"] = {
        "searchStr": xml_tree_view.get("@searchStr", ""),
        "showStatDifferences": str_to_bool(xml_tree_view.get("@showStatDifferences", "True")),
    }

    """Tree/Specs"""
    xml_tree = xml_PoB["Tree"]
    json_PoB["Tree"] = {
        "activeSpec": int(xml_tree.get("@activeSpec", "1")) - 1,
        "Specs": [],
    }
    if type(xml_tree["Spec"]) is dict:  # list or dict if only one
        xml_tree["Spec"] = [xml_tree["Spec"]]
    for xml_spec in xml_tree["Spec"]:
        spec = {
            "title": remove_lua_colours(xml_spec.get("@title", "Default")),
            "treeVersion": xml_spec.get("@treeVersion", _VERSION_str),
            "classId": int(xml_spec.get("@classId", "0")),
            "ascendClassId": int(xml_spec.get("@ascendClassId", "0")),
            "nodes": xml_spec.get("@nodes", starting_scion_node),
            "masteryEffects": xml_spec.get("@masteryEffects", ""),
            "URL": xml_spec.get("URL", "https://www.pathofexile.com/passive-skill-tree/AAAABgAAAAAA"),
            "Sockets": "",
            "Overrides": "",
        }
        if xml_spec["Sockets"]:
            str_sockets = ""
            for socket in xml_spec["Sockets"]["Socket"]:
                str_sockets += f"{{{socket['@nodeId']},{socket['@itemId']}}}"
            spec["Sockets"] = str_sockets.rstrip(",")
        # Ignoring Overrides
        json_PoB["Tree"]["Specs"].append(spec)

    """Skills/Gems"""
    xml_skills = xml_PoB["Skills"]
    skills = {
        "activeSkillSet": int(get_param_value(xml_skills.get("@activeSkillSet", "1"), "1")) - 1,
        "sortGemsByDPSField": xml_skills.get("@sortGemsByDPSField", "CombinedDPS"),
        "sortGemsByDPS": str_to_bool(get_param_value(xml_skills.get("@sortGemsByDPS", "True"), "True")),
        "defaultGemQuality": int(get_param_value(xml_skills.get("@defaultGemQuality", "0"), "0")),
        "defaultGemLevel": xml_skills.get("@defaultGemLevel", "normalMaximum"),
        "showSupportGemTypes": xml_skills.get("@showSupportGemTypes", "ALL"),
        "showAltQualityGems": str_to_bool(get_param_value(xml_skills.get("@showAltQualityGems", "True"), "True")),
        "SkillSets": [],
    }
    if type(xml_skills["SkillSet"]) is dict:  # list or dict if only one
        xml_skills["SkillSet"] = [xml_skills["SkillSet"]]
    for xml_skillset in xml_skills["SkillSet"]:
        skillset = {
            "id": int(get_param_value(xml_skillset.get("@id", "1"), "1")) - 1,
            "title": remove_lua_colours(xml_skillset.get("@title", "Default")),
            "SGroups": [],
        }
        if type(xml_skillset.get("Skill", bad_text)) is dict:  # list or dict if only one
            xml_skillset["Skill"] = [xml_skillset["Skill"]]
        for xml_sgroup in xml_skillset.get("Skill", []):
            xml_gem = xml_sgroup.get("Gem", bad_text)
            sgroup = {
                "enabled": str_to_bool(get_param_value(xml_sgroup.get("@enabled", "True"), "True")),
                "label": remove_lua_colours(xml_sgroup.get("@label", "")),
                "source": remove_lua_colours(xml_sgroup.get("@source", "")),
                "mainActiveSkill": int(get_param_value(xml_sgroup.get("@mainActiveSkill", "1"), "1")) - 1,
                "mainActiveSkillCalcs": int(get_param_value(xml_sgroup.get("@mainActiveSkillCalcs", "1"), "1")) - 1,
                "includeInFullDPS": str_to_bool(get_param_value(xml_sgroup.get("@includeInFullDPS", "False"), "False")),
                "slot": xml_sgroup.get("@slot", ""),
                "Gems": [],
            }
            # Some socket groups have no skills in them as content creators just use the label.
            if xml_gem != bad_text:
                if type(xml_gem) is dict:  # list or dict if only one
                    xml_gem = [xml_gem]
                for xml_gem in xml_gem:
                    """
                    new >=v3.23
                    gemId="Metadata/Items/Gems/SupportGemFeedingFrenzy" 	->base_gems skillId
                    variantId="FeedingFrenzySupport" 						->base_gems Dict Key
                    skillId="SupportMinionOffensiveStance" 					->base_gems grantedEffectId
                    nameSpec="Feeding Frenzy"								->base_gems grantedEffect.name

                    old <3.23
                    gemId="Metadata/Items/Gems/SupportGemFeedingFrenzy"		->base_gems skillId
                    skillId="FeedingFrenzySupport"							->base_gems Dict Key
                    nameSpec="Feeding Frenzy"								->base_gems grantedEffect.name
                    """
                    variantId = xml_gem.get("@variantId", bad_text)
                    if variantId == bad_text:
                        # pre 3.23 xml
                        xml_gem["@variantId"] = xml_gem.get("@skillId", "")
                        xml_gem["@skillId"] = ""

                    gem = {
                        "enabled": str_to_bool(get_param_value(xml_gem.get("@enabled", "True"), "True")),
                        "nameSpec": xml_gem.get("@nameSpec", ""),
                        "variantId": xml_gem.get("@variantId", ""),
                        "skillId": xml_gem.get("@skillId", ""),
                        "level": int(get_param_value(xml_gem.get("@level", "1"), "1")),
                        "qualityId": xml_gem.get("@qualityId", ""),
                        "quality": int(get_param_value(xml_gem.get("@quality", "0"), "0")),
                        "count": int(get_param_value(xml_gem.get("@count", "1"), "1")),
                        "enableGlobal1": str_to_bool(get_param_value(xml_gem.get("@enableGlobal1", "True"), "True")),
                        "enableGlobal2": str_to_bool(get_param_value(xml_gem.get("@enableGlobal2", "True"), "True")),
                        # "gemId": xml_gem.get("@gemId", ""),
                    }
                    if xml_gem.get("@skillMinion", ""):
                        gem["skillMinion"] = xml_gem.get("@skillMinion")
                        gem["skillMinionSkillCalcs"] = int(xml_gem.get("@skillMinionSkill", "1"))
                        gem["skillMinionSkill"] = int(xml_gem.get("@skillMinionSkill", "1"))
                        gem["skillMinionCalcs"] = xml_gem.get("@skillMinionCalcs")
                    sgroup["Gems"].append(gem)
            skillset["SGroups"].append(sgroup)
        skills["SkillSets"].append(skillset)

    json_PoB["Skills"] = skills

    """Items"""
    xml_items = xml_PoB["Items"]
    json_PoB["Items"]["activeItemSet"] = int(get_param_value(xml_items.get("@activeItemSet", "1"), "1")) - 1
    # Items
    if type(xml_items["Item"]) is dict:  # list or dict if only one
        xml_items["Item"] = [xml_items["Item"]]
    for xml_item in xml_items["Item"]:
        json_PoB["Items"]["Items"].append(load_item_from_xml(xml_item["#text"], xml_item.get("@id", 0)))
    # ItemSets
    json_PoB["Items"]["ItemSets"].clear()  # get rid of the default itemset
    if type(xml_items["ItemSet"]) is dict:  # list or dict if only one
        xml_items["ItemSet"] = [xml_items["ItemSet"]]
    for xml_itemset in xml_items["ItemSet"]:
        json_set = {
            "title": remove_lua_colours(xml_itemset.get("@title", "Default")),
            "id": int(get_param_value(xml_itemset.get("@id", "0"), "0")) - 1,
            "useSecondWeaponSet": str_to_bool(xml_itemset.get("@useSecondWeaponSet", "False")),
        }
        # The xml has too much slot info, like "Belt Abyssal Socket 6". Use our dictionary to pick out wanted entries.
        slots = {}
        for xml_slot in xml_itemset["Slot"]:
            try:
                # any errors here will just result in a slot not being set.
                name = xml_slot.get("@name", "")
                _id = get_param_value(xml_slot.get("@itemId", "0"), "0")
                if name and _id != "0" and name in empty_item_slots_dict.keys():
                    slots[name] = {"itemId": int(_id), "itemPbURL": xml_slot.get("@itemPbURL", "")}
            except KeyError:
                pass
        json_set["Slots"] = slots
        for s_id in xml_itemset.get("SocketIdURL", []):
            name = s_id.get("@name", "")
            if name:
                json_set.setdefault("SocketIdURL", []).append(
                    {"name": name, "nodeId": int(s_id.get("@nodeId", "")), "itemPbURL": s_id.get("@itemPbURL", "")}
                )
        json_PoB["Items"]["ItemSets"].append(json_set)

    return new_build


def save_item_to_xml(_item):
    """
    Save internal structures back to a xml object. Not used.

    :return: xml.etree.ElementTree:
    """

    text = f"Rarity: {_item['Rarity']}\n"
    text += _item.get("title", "") and f"{_item['title']}\n{_item['base_name']}\n" or f"{_item['base_name']}\n"
    for _var, _name in _item.get("Variant Entries", {}).get("base_name", {}).items():
        text = f"{{variant:{str(_var)}}}{_name}\n"
    for influence in _item.get("Influences", []):
        text += f"{influence}\n"
    if _item.get("Selected Variant", 0):
        for variant in _item.get("Variants", []):
            text += f"Variant: {variant}\n"
        text += f"Selected Variant: {str(_item['Selected Variant'])}\n"
    for attrib, value in _item["Attribs"].items():
        text += f"{attrib}: {str(value)}\n"
    for attrib, value in _item["Requires"].items():
        if attrib == "Level":
            text += f"LevelReq: {str(value)}\n"
        else:
            text += f"{attrib}: {str(value)}\n"

    text += f"Implicits: {len(_item['Implicits'])}\n"
    for mod in _item["Implicits"]:
        text += f"{mod}\n"
    for mod in _item["Explicits"]:
        text += f"{mod}\n"

    if _item.get("Corrupted", False):
        text += "Corrupted"

    if _item.get("Selected Variant", 0):
        return ET.fromstring(f'<Item variant="{str(_item["Selected Variant"])}" id="{str(_item["id"])}">{text}</Item>')
    else:
        return ET.fromstring(f'<Item id="{str(_item["id"])}">{text}</Item>')
    # save


def save_to_xml(filename, build):
    """
    Everything needed to convert internal dict to xml
    :param filename:
    :param build: Build() class
    :return: N/A
    """

    def get_value_s_type(_value):
        match _value:
            # bool() must come before int
            case bool():
                _type = "boolean"
                _v = f"{_value}"
            case int() | float():
                _type = "number"
                _v = f"{_value}"
            case _:
                _type = "string"
                _v = _value
        return _v, _type

    # print(f"save_to_xml: {filename}")

    # Flag to reread the written file and change ~^ back to newlines.
    customMods = False
    build_xml = ET.ElementTree(ET.fromstring("<PathOfBuilding></PathOfBuilding>"))
    xml_root = build_xml.getroot()

    json_config = build["PathOfBuilding"]["Config"]

    """Build"""
    json_build = build["PathOfBuilding"]["Build"]
    _build = (
        f'<Build level="{str(json_build["level"])}" targetVersion="{json_build["targetVersion"]}" '
        f'pantheonMajorGod="{json_config["Input"]["pantheonMajorGod"]}" bandit="{json_config["Input"]["bandit"]}" '
        f'className="{json_build["className"]}" ascendClassName="{json_build["ascendClassName"]}" '
        f'characterLevelAutoMode="{bool_to_str(json_build["characterLevelAutoMode"])}" '
        f'mainSocketGroup="{str(json_build["mainSocketGroup"]+1)}" viewMode="{json_build["viewMode"]}" '
        f'pantheonMinorGod="{json_config["Input"]["pantheonMinorGod"]}" >'
        f"</Build>"
    )
    xml_build = ET.fromstring(_build)
    for stat, value in json_build["PlayerStat"].items():
        xml_build.append(ET.fromstring(f'<PlayerStat stat="{stat}" value="{str(value)}"/>'))
    for stat, value in json_build["MinionStat"].items():
        xml_build.append(ET.fromstring(f'<MinionStat stat="{stat}" value="{str(value)}"/>'))
    tld = json_build["TimelessData"]
    xml_build.append(
        ET.fromstring(
            f'<TimelessData devotionVariant2="{str(tld["devotionVariant2"])}" searchListFallback="{tld["searchListFallback"]}" '
            f'searchList="{tld["searchList"]}" socketFilterDistance="{str(tld["socketFilterDistance"])}" '
            f'devotionVariant1="{str(tld["devotionVariant1"])}" />'
        )
    )
    xml_root.append(xml_build)

    """Import"""
    json_import = build["PathOfBuilding"]["Import"]
    xml_import = ET.fromstring(
        f'<Import lastCharacterHash="{json_import.get("lastCharacterHash","")}" lastRealm="{json_import.get("lastRealm","")}"'
        f' exportParty="{bool_to_str(json_import.get("exportParty","False"))}" lastAccountHash="{json_import.get("lastAccountHash","")}"/>'
    )
    xml_root.append(xml_import)

    """Tree"""
    json_tree = build["PathOfBuilding"]["Tree"]
    xml_tree = ET.fromstring(f'<Tree activeSpec="{str(json_tree["activeSpec"]+1)}"> </Tree>')
    for spec in json_tree["Specs"]:
        _spec = (
            f'<Spec masteryEffects="{str(spec["masteryEffects"])}" title="{spec["title"]}" ascendClassId="{str(spec["ascendClassId"])}" '
            f'nodes="{str(spec["nodes"])}" secondaryAscendClassId="0" '
            f'treeVersion="{spec["treeVersion"]}" classId="{str(spec["ascendClassId"])}" />'
        )
        xml_spec = ET.fromstring(_spec)
        xml_spec.append(ET.fromstring(f'<URL>{spec["URL"]}</URL>'))
        xml_sockets = ET.fromstring(f"<Sockets/>")
        xml_overides = ET.fromstring(f"<Overrides/>")
        sockets = re.findall(r"{(\d+),(\d+)}", spec["Sockets"])
        for socket in sockets:
            xml_sockets.append(ET.fromstring(f'<Socket nodeId="{str(socket[0])}" itemId="{str(socket[1])}"/>'))
        # for nodeId, itemId in spec["Overrides"].items():
        #     xml_overides.append(ET.fromstring(f'<Override nodeId="{str(nodeId)}" itemId="{str(itemId)}"/>'))
        xml_spec.append(xml_sockets)
        xml_spec.append(xml_overides)
        xml_tree.append(xml_spec)
    xml_root.append(xml_tree)

    """Notes"""
    xml_root.append(ET.fromstring(f'<Notes>{build["PathOfBuilding"]["Notes"]}</Notes>'))

    """Skills"""
    json_skills = build["PathOfBuilding"]["Skills"]
    skills = (
        f'<Skills sortGemsByDPSField="{json_skills["sortGemsByDPSField"]}" activeSkillSet="{str(json_skills["activeSkillSet"]+1)}" '
        f'sortGemsByDPS="{bool_to_str(json_skills["sortGemsByDPS"])}" defaultGemQuality="{str(json_skills["defaultGemQuality"])}" '
        f'defaultGemLevel="{json_skills["defaultGemLevel"]}" showSupportGemTypes="{json_skills["showSupportGemTypes"]}" '
        f'showAltQualityGems="{bool_to_str(json_skills["showAltQualityGems"])}" />'
    )
    xml_skills = ET.fromstring(skills)
    for _set in json_skills["SkillSets"]:
        xml_set = ET.fromstring(f'<SkillSet id="{str(_set["id"])}"/>')
        for _sg in _set["SGroups"]:
            source_text = ""
            if _sg.get("source", ""):
                # we cannot have a 'source=""' in socket group. luaPoB will reject the whole socket group.
                source_text = f'source="{_sg.get("source","")}" '
            text_sg = (
                f'<Skill mainActiveSkillCalcs="{str(_sg["mainActiveSkillCalcs"]+1)}" '
                f'includeInFullDPS="{bool_to_str(_sg["includeInFullDPS"])}" label="{_sg["label"]}" {source_text} '
                f'enabled="{bool_to_str(_sg["enabled"])}" slot="{_sg["slot"]}" '
                f'mainActiveSkill="{str(_sg["mainActiveSkill"]+1)}" />'
            )
            xml_sg = ET.fromstring(text_sg)
            for _gem in _sg["Gems"]:
                if _gem.get("skillMinion", ""):
                    text_gem = (
                        f'<Gem enableGlobal2="{bool_to_str(_gem["enableGlobal2"])}" '
                        f'skillMinionSkillCalcs="{str(_gem["skillMinionSkillCalcs"])}" '
                        f'level="{str(_gem["level"])}" skillId="{_gem["skillId"]}" skillMinionSkill="{str(_gem["level"])}" '
                        f'quality="{str(_gem["quality"])}" enableGlobal1="{bool_to_str(_gem["enableGlobal1"])}" '
                        f'enabled="{bool_to_str(_gem["enabled"])}" count="{str(_gem["count"])}" nameSpec="{_gem["nameSpec"]}" '
                        f'skillMinion="{_gem["skillMinion"]}" />'
                    )
                else:
                    text_gem = (
                        f'<Gem enableGlobal2="{bool_to_str(_gem["enableGlobal2"])}" level="{str(_gem["level"])}" '
                        f'gemId="" variantId="{_gem["variantId"]}" skillId="{_gem["skillId"]}" quality="{str(_gem["quality"])}" '
                        f' enableGlobal1="{bool_to_str(_gem["enableGlobal1"])}" enabled="{bool_to_str(_gem["enabled"])}" '
                        f'count="{str(_gem["count"])}" nameSpec="{_gem["nameSpec"]}"/>'
                    )
                xml_sg.append(ET.fromstring(text_gem))
            xml_set.append(xml_sg)
        xml_skills.append(xml_set)
    xml_root.append(xml_skills)

    """Calcs"""
    json_calcs = build["PathOfBuilding"]["Calcs"]
    xml_calcs = ET.fromstring(f"<Calcs/>")
    for _name, _value in json_calcs["Input"].items():
        _value, value_type = get_value_s_type(_value)
        xml_calcs.append(ET.fromstring(f'<Input name="{_name}" {value_type}="{_value}"/>'))
    for _name, _value in json_calcs["Sections"].items():
        xml_calcs.append(
            ET.fromstring(f'<Section subsection="{_name}" collapsed="{bool_to_str(_value["collapsed"])}" id="{_value["id"]}"/>')
        )
    xml_root.append(xml_calcs)

    """TreeView"""
    json_tv = build["PathOfBuilding"]["TreeView"]
    tv = (
        f'<TreeView searchStr="{json_tv["searchStr"]}" zoomY="0" zoomLevel="3" '
        f'showStatDifferences="{bool_to_str(json_tv["showStatDifferences"])}" zoomX="0" />'
    )
    xml_root.append(ET.fromstring(tv))

    """Items"""
    json_items = build["PathOfBuilding"]["Items"]
    items = f'<Items activeItemSet="{str(json_items["activeItemSet"]+1)}" />'
    xml_items = ET.fromstring(items)
    for _item in json_items["Items"]:
        xml_items.append(save_item_to_xml(_item))
    for _set in json_items["ItemSets"]:
        xml_itemset = ET.fromstring(f'<ItemSet useSecondWeaponSet="{bool_to_str(_set["useSecondWeaponSet"])}" id="{str(_set["id"]+1)}" />')
        xml_items.append(xml_itemset)
        for slot, value in _set["Slots"].items():
            xml_itemset.append(ET.fromstring(f'<Slot itemPbURL="{value["itemPbURL"]}" name="{slot}" itemId="{str(value["itemId"])}"/>'))
        if _set.get("SocketIdURL", []):
            for slot in _set["SocketIdURL"]:
                xml_itemset.append(
                    ET.fromstring(f'<SocketIdURL nodeId="{str(slot["nodeId"])}" name="{slot["name"]}" itemPbURL="{slot["itemPbURL"]}" />')
                )
    xml_root.append(xml_items)

    """Config"""
    json_config = build["PathOfBuilding"]["Config"]
    xml_config = ET.fromstring(f"<Config/>")
    for _name, _value in json_config["Input"].items():
        if _name == "customMods":
            xml_config.append(ET.fromstring(f'<Input name="customMods" string="{_value}"/>'))
            customMods = True
        else:
            _value, value_type = get_value_s_type(_value)
            xml_config.append(ET.fromstring(f'<Input name="{_name}" {value_type}="{_value}"/>'))
    for _name, _value in json_config["Placeholder"].items():
        _value, value_type = get_value_s_type(_value)
        xml_config.append(ET.fromstring(f'<Placeholder name="{_name}" {value_type}="{_value}"/>'))
    xml_root.append(xml_config)

    # # build.text = ""
    # print_a_xml_element(build_xml)
    # build_xml.append(build)
    # print_a_xml_element(build_xml)

    # xml_import = xml_root.find("Import")
    # if xml_import is not None:
    #     last_account_hash = xml_import.get("lastAccountHash", "")
    #     last_character_hash = xml_import.get("lastCharacterHash", "")
    #     last_realm = xml_import.get("lastRealm", "")
    #     last_league = xml_import.get("lastLeague", "")
    # xml_calcs = xml_root.find("Calcs")
    # xml_skills = xml_root.find("Skills")
    # xml_tree = xml_root.find("Tree")
    # xml_notes = xml_root.find("Notes")
    # xml_notes_html = xml_root.find("NotesHTML")
    # # lua version doesn't have NotesHTML, expect it to be missing
    # if xml_notes_html is None:
    #     xml_notes_html = ET.Element("NotesHTML")
    #     xml_root.append(xml_notes_html)
    # xml_tree_view = xml_root.find("TreeView")
    # xml_items = xml_root.find("Items")
    # xml_config = xml_root.find("Config")

    # print_a_xml_element(xml_root)

    if filename:
        write_xml(filename, build_xml)
        # rewrite ~^ to newlines
        if customMods:
            write_v1_custom_mods(filename)
    else:
        return xml_root
