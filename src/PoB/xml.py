from pathlib import Path, WindowsPath
import copy
import re
import xml.etree.ElementTree as ET
import xmltodict

from PoB.constants import _VERSION_str, default_view_mode, empty_build, empty_item_dict, starting_scion_node

""" ################################################### XML ################################################### """

default_spec_xml = f"""<Spec title="Default" classId="0" ascendClassId="0" masteryEffects="" nodes="{starting_scion_node}" 
treeVersion="{_VERSION_str}"></Spec>"""
default_skill_set_xml = """<SkillSet id="1" title="Default">
  <Skill mainActiveSkillCalcs="1" includeInFullDPS="false" label="" enabled="true" slot="" mainActiveSkill="1"></Skill>
</SkillSet>"""

empty_socket_group_xml = """<Skill mainActiveSkillCalcs="1" includeInFullDPS="false" label=""
enabled="true" slot="" mainActiveSkill="1"/>"""

empty_gem_xml = """<Gem enableGlobal2="false" level="1" enableGlobal1="true" skillId="" qualityId="Default"
gemId="" enabled="true" quality="0" count="1" nameSpec=""/>"""

empty_build_xml = f"""
<PathOfBuilding>
    <Build version="2" level="1" targetVersion="3_0" bandit="None" className="Scion" ascendClassName="None"
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


def str_to_bool(in_str):
    """
    Return a boolean from a string. As the settings could be manipulated by a human, we can't trust eval()
      EG: eval('os.system(`rm -rf /`)')
    :param: in_str: String: The setting to be evaluated
    :returns: True if it looks like it could be true, otherwise False
    """
    return in_str.lower() in ("yes", "true", "t", "1", "on")


def index_exists(_list_or_dict, index):
    """
    Test if a list contains a given index
    :param _list_or_dict: object to be tested
    :param index: index to be tested
    :return: Boolean: True / False
    """
    try:
        _l = _list_or_dict[index]
        return True
    except (IndexError, KeyError, TypeError):
        return False


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


def read_xml_as_dict(filename):
    """
    Reads a XML file
    :param filename: Name of xml to be read
    :returns: A dictionary of the contents of the file
    """
    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r") as xml_file:
                xml_content = xml_file.read()
                _dict = xmltodict.parse(xml_content)
                return _dict
        # parent of IOError, OSError *and* WindowsError where available
        except EnvironmentError:
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
    Read the v1 xml customMods. These are line separated and will be lost when read from XML
    :param filename: Name of xml to be read
    :return: str: with \n encoded in it.
    """
    custom_mods = []
    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r") as xml_file:
                string = xml_file.read()
                m = re.findall(r'<Input (.*?)"/>', string, re.DOTALL | re.MULTILINE | re.IGNORECASE)
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


def load_item_from_xml(xml, debug_lines=False):
    """
    Load internal structures from the free text version of item's xml

    :param xml: ET.element: xml of the item
    :param debug_lines: Temporary to debug the process
    :return: boolean
    """

    influencers = (
        "Shaper Item",
        "Elder Item",
        "Warlord Item",
        "Hunter Item",
        "Crusader Item",
        "Redeemer Item",
        "Searing Exarch Item",
        "Eater of Worlds Item",
    )
    # Entries in the item Free text
    strings = (
        "Armour",
        "Energy Shield",
        "Evasion",
        "League",
        "Radius",
        "Sockets",
        "Source",
        "Talisman Tier",
        "Unique ID",
        "Upgrade",
    )
    integers = ("Item Level", "LevelReq", "Limited to" "Quality")
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

            case "Variant":
                json_item["Variants"].append(n.group(2))
            case "Selected Variant":
                json_item["Current Variant"] = int(n.group(2)) - 1
            case "Prefix" | "Suffix":
                json_item["Crafted"][tag].append(n.group(2))
            case "Has Alt Variant":
                json_item["alt_variants"][1] = 0
            case "Selected Alt Variant":
                json_item["alt_variants"][1] = int(n.group(2))
            case "Has Alt Variant Two":
                json_item["alt_variants"][2] = 0
            case "Selected Alt Variant Two":
                json_item["alt_variants"][2] = int(n.group(2))
            case "Has Alt Variant Three":
                json_item["alt_variants"][3] = 0
            case "Selected Alt Variant Three":
                json_item["alt_variants"][3] = int(n.group(2))
            case "Has Alt Variant Four":
                json_item["alt_variants"][4] = 0
            case "Selected Alt Variant Four":
                json_item["alt_variants"][4] = int(n.group(2))
            case "Has Alt Variant Five":
                json_item["alt_variants"][5] = 0
            case "Selected Alt Variant Five":
                json_item["alt_variants"][5] = int(n.group(2))

    # Deep copy or else we end up editing the constant
    json_item = copy.deepcopy(empty_item_dict)

    # debug_lines = True
    items_free_text = xml["#text"]
    json_item["id"] = xml.get("@id", 0)
    if "Alt Variant" in items_free_text:
        json_item["alt_variants"] = {}
    if "Variant:" in items_free_text:
        json_item["Variants"] = []
    if "Crafted:" in items_free_text:
        json_item["Crafted"] = {"Prefix": [], "Suffix": []}

    # split lines into a list, removing any blank lines, leading & trailing spaces.
    #   stolen from https://stackoverflow.com/questions/7630273/convert-multiline-into-list
    lines = [y for y in (x.strip(" \t\r\n") for x in items_free_text.splitlines()) if y]
    # The first line has to be rarity !!!!
    line = lines.pop(0)
    if "rarity" not in line.lower():
        print("Error: Dave, I don't know what to do with this:\n", items_free_text)
        return False
    m = re.search(r"(.*): (.*)", line)
    json_item["rarity"] = m.group(2).upper()
    # The 2nd line is either the title or the name of a magic/normal item. This is why Rarity is first.
    line = lines.pop(0)
    if json_item["rarity"] in ("NORMAL", "MAGIC"):
        json_item["base_name"] = line
    else:
        json_item["title"] = line
        line = lines.pop(0)
        if "{variant" in line:
            while "{variant" in line:
                v = re.search(r"{variant:([\d,]+)}(.*)", line)
                _variant_numbers = v.group(1).split(",")
                # _variant_numbers is always a list (of str), even if it contains one entry.
                for _var in _variant_numbers:
                    json_item["Variants"].setdefault("base_name", {})[int(_var)] = v.group(2)
                if "{variant" in lines[0]:
                    line = lines.pop(0)
        else:
            json_item["base_name"] = line

    if debug_lines:
        print("a", len(lines), lines)

    """ So the first three lines/Entries are gone, so it's game on. They can come in almost any order """
    # lets get all the colon(:) separated variables first and remove them from the lines list
    # stop when we get to implicits, or the end (eg: Tabula Rasa)
    line_idx, implicits_idx, explicits_idx = (0, -1, -1)
    # We can't use enumerate as we are changing the list as we move through
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
            elif line.startswith("Requires"):
                # No colon for Requires
                m = re.search(r"Requires (.*)", line)
                for req in m.group(1).split(","):
                    if "level" in req.lower():
                        r = re.search(r"(\w+) (\d+)", f"{req}")
                        json_item["Requires"]["level_req"] = int(r.group(2))
                    elif "class" in req.lower():
                        r = re.search(r"(\w+) (\w+)", f"{req}")
                        json_item["Requires"]["Class"] = r.group(2)
                    else:
                        # Str nnn, etc
                        r = re.search(r"(\w+) (\d+)", f"{req}")
                        json_item["Requires"][r.group(1)] = int(r.group(2))
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
        print("b", len(lines), lines)
    # every thing that is left, from explicits_idx, is explicits ... and some other stuff
    # for idx in range(explicits_idx, len(lines) + 1):
    while len(lines) > 0:
        line = lines.pop(explicits_idx)
        # Corrupted is not a mod, but will get caught in explicits due to crap data design.
        # Some items have things like UniqueID in the middle of this too.
        if "Corrupted" in line:
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

    return json_item
    # load_item_from_xml


def load_from_xml(filename):
    """
    Convert a lua PoB xml to a dict.
    lua PoB won't put a single Gem, Item, Spec, etc in a list. It will just appear as a single dict()
    So there are lots of checks for this and adding a single entry into a list().
    lua PoB is 1 based in it's counting, pyPob is 0 based
    :param filename: str:
    :return: dict
    """

    def get_input_values(_src, _dst):
        """
        Get a list of {"@name": "key", "@string: "value"} and add it to the destination dictionary

        :param _src: list
        :param _dst: dict
        :return:
        """
        if _src and _dst:
            for _dict in _src:
                # _name = _dict["@name"]
                # input.pop("@name")
                _name = _dict.pop("@name")
                _value = ""
                key = [key for key in _dict.keys()]
                match key[0]:
                    case "@string":
                        _value = _dict["@string"]
                    case "@number":
                        _value = int(_dict["@number"])
                    case "@number":
                        _value = str_to_bool(_dict["@number"])
                _dst[_name] = _value

    # ToDo: Complete
    xml_PoB = read_xml_as_dict(filename)
    if xml_PoB is None:
        return None
    new_build = empty_build
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
        for stat in stats:
            name = stat.get("@stat", "")
            if name:
                value = stat.get("@value", "")
                if "." in value:
                    json_build[stat_type][name] = float(stat.get("@value", "0.0"))
                else:
                    json_build[stat_type][name] = int(stat.get("@value", "0"))
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
            "exportParty": str_to_bool(xml_import.get("@lastAccountHash", "False")),
            "lastAccountHash": xml_import.get("@lastAccountHash", ""),
            "lastCharacterHash": xml_import.get("@lastCharacterHash", ""),
            "lastRealm": xml_import.get("@lastRealm", ""),
            "lastLeague": xml_import.get("@lastLeague", ""),
        }

    """Calcs"""
    xml_calcs = xml_PoB["Calcs"]
    get_input_values(xml_calcs["Input"], json_PoB["Calcs"]["Input"])
    for section in xml_calcs["Section"]:
        json_PoB["Calcs"]["Sections"][section["@subsection"]] = {"collapsed": section["@collapsed"], "id": section["@id"]}

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
        # "zoomY": float(xml_tree_view.get("@zoomY", "0")),
        # "zoomLevel": int(xml_tree_view.get("@zoomLevel", "3")),
        # "zoomX": float(xml_tree_view.get("@zoomX", "0")),
        "showStatDifferences": str_to_bool(xml_tree_view.get("@showStatDifferences", "True")),
    }

    """Tree/Specs"""
    xml_tree = xml_PoB["Tree"]
    json_PoB["Tree"] = {
        "activeSpec": int(xml_tree.get("@activeSpec", "1")) - 1,
        "Specs": [],
    }
    if type(xml_tree["Spec"]) is dict:
        xml_tree["Spec"] = [xml_tree["Spec"]]
    for xml_spec in xml_tree["Spec"]:
        spec = {
            "title": xml_spec.get("@title", "Default"),
            "treeVersion": xml_spec.get("@treeVersion", _VERSION_str),
            "classId": int(xml_spec.get("@classId", "0")),
            "ascendClassId": int(xml_spec.get("@ascendClassId", "0")),
            "nodes": xml_spec.get("@nodes", starting_scion_node),
            "masteryEffects": xml_spec.get("@masteryEffects", ""),
            "URL": xml_spec.get("@URL", "https://www.pathofexile.com/passive-skill-tree/AAAABgAAAAAA"),
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
        "activeSkillSet": int(xml_skills.get("@activeSkillSet", "1")) - 1,
        "sortGemsByDPSField": xml_skills.get("@sortGemsByDPSField", "CombinedDPS"),
        "sortGemsByDPS": str_to_bool(xml_skills.get("@sortGemsByDPS", "True")),
        "defaultGemQuality": int(xml_skills.get("@defaultGemQuality", "0")),
        "defaultGemLevel": xml_skills.get("@defaultGemLevel", "normalMaximum"),
        "showSupportGemTypes": xml_skills.get("@showSupportGemTypes", "ALL"),
        "showAltQualityGems": str_to_bool(xml_skills.get("@showAltQualityGems", "True")),
        "SkillSets": [],
    }
    if type(xml_skills["SkillSet"]) is dict:
        xml_skills["SkillSet"] = [xml_skills["SkillSet"]]
    for xml_skillset in xml_skills["SkillSet"]:
        skillset = {
            "id": int(xml_skillset.get("@id", "1")) - 1,
            "title": xml_skillset.get("@title", "Default"),
            "SGroups": [],
        }
        if type(xml_skillset["Skill"]) is dict:
            xml_skillset["Skill"] = [xml_skillset["Skill"]]
        for xml_sgroup in xml_skillset["Skill"]:
            sgroup = {
                "enabled": str_to_bool(xml_sgroup.get("@enabled", "True")),
                "label": xml_sgroup.get("@label", ""),
                "mainActiveSkillCalcs": int(xml_sgroup.get("@mainActiveSkillCalcs", "0")),
                "includeInFullDPS": str_to_bool(xml_sgroup.get("@includeInFullDPS", "False")),
                "slot": xml_sgroup.get("@slot", ""),
                "mainActiveSkill": int(xml_sgroup.get("@mainActiveSkill", "0")),
                "Gems": [],
            }
            if type(xml_sgroup["Gem"]) is dict:
                xml_sgroup["Gem"] = [xml_sgroup["Gem"]]
            for xml_gem in xml_sgroup["Gem"]:
                gem = {
                    "enabled": str_to_bool(xml_sgroup.get("@enabled", "True")),
                    "nameSpec": xml_gem.get("@nameSpec", ""),
                    "skillId": xml_gem.get("@skillId", ""),
                    "level": int(xml_sgroup.get("@level", "20")),
                    "qualityId": xml_gem.get("@qualityId", ""),
                    "quality": int(xml_sgroup.get("@quality", "0")),
                    "count": int(xml_sgroup.get("@count", "1")),
                    "enableGlobal1": str_to_bool(xml_sgroup.get("@enableGlobal1", "True")),
                    "enableGlobal2": str_to_bool(xml_sgroup.get("@enableGlobal2", "True")),
                    "gemId": xml_gem.get("@gemId", ""),
                }
                sgroup["Gems"].append(gem)
            skillset["SGroups"].append(sgroup)
        skills["SkillSets"].append(skillset)

    json_PoB["Skills"] = skills

    """Items"""
    xml_items = xml_PoB["Items"]
    json_PoB["Items"]["activeItemSet"] = int(xml_items.get("@activeItemSet", "1")) - 1
    # Items
    if type(xml_items["Item"]) is dict:
        xml_items["Item"] = [xml_items["Item"]]
    for xml_item in xml_items["Item"]:
        json_PoB["Items"]["Items"].append(load_item_from_xml(xml_item))
    # ItemSets
    json_PoB["Items"]["ItemSets"].clear()  # get rid of the default itemset
    if type(xml_items["ItemSet"]) is dict:
        xml_items["ItemSet"] = [xml_items["ItemSet"]]
    for xml_itemset in xml_items["ItemSet"]:
        json_set = {
            "title": xml_itemset.get("@title", ""),
            "id": int(xml_itemset.get("@id", "0")) - 1,
            "useSecondWeaponSet": str_to_bool(xml_itemset.get("@useSecondWeaponSet", "False")),
            "Slots": {},
        }
        for slot in xml_itemset["Slot"]:
            try:
                # any errors here will just result in a slot not being set.
                json_set["Slots"][slot["@name"]] = {"itemId": int(slot["@itemId"]), "itemPbURL": slot.get("@itemPbURL", "")}
            except KeyError:
                pass
        json_PoB["Items"]["ItemSets"].append(json_set)

    return new_build


def save_to_xml(filename, build):
    """
    Everything needed to convert internal dict to xml
    :param filename:
    :param build: Build() class
    :return: N/A
    """
    # ToDo: Complete
    xml_build = empty_build_xml
    xml_root = xml_build.getroot()
    xml_import = xml_root.find("Import")
    if xml_import is not None:
        last_account_hash = xml_import.get("lastAccountHash", "")
        last_character_hash = xml_import.get("lastCharacterHash", "")
        last_realm = xml_import.get("lastRealm", "")
        last_league = xml_import.get("lastLeague", "")
    xml_calcs = xml_root.find("Calcs")
    xml_skills = xml_root.find("Skills")
    xml_tree = xml_root.find("Tree")
    xml_notes = xml_root.find("Notes")
    xml_notes_html = xml_root.find("NotesHTML")
    # lua version doesn't have NotesHTML, expect it to be missing
    if xml_notes_html is None:
        xml_notes_html = ET.Element("NotesHTML")
        xml_root.append(xml_notes_html)
    xml_tree_view = xml_root.find("TreeView")
    xml_items = xml_root.find("Items")
    xml_config = xml_root.find("Config")
