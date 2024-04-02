"""
Functions for reading and writing xml and json

This is a base PoB class. It doesn't import any other PoB classes

!!!! read_xml_as_dict(filename) stays in this module as it is used by get_file_info !!!!
"""

from copy import deepcopy
from pathlib import Path, WindowsPath
import json
import os
import xml
import xmltodict

from PoB.constants import ColourCodes
from PoB.utils import html_colour_text


def get_file_info(settings, filename, max_length, max_filename_width=40, html=True, menu=False):
    """
    Open the xml and get the class information, level and version. Format a line for display on the listbox.
    Take into account the maximum width of the listbox and trim names as needed.

    :param settings: Settings():
    :param filename: name of file in current directory.
    :param max_length: int: of the longest name.
    :param max_filename_width: int: Maximum number of characters of the filename to be shown.
    :param html: bool: If True return the text as html formatted.
    :param menu: bool: Menu entry text is covered by QSS
    :return: str, str: "", "" if invalid xml, or colourized name and class name.
    """
    if type(filename) is Path or type(filename) is WindowsPath:
        filename = filename.name
    if "json" in filename:
        try:
            _file = read_json(filename)
            pre = ""
            version = 2
        except (json.JSONDecodeError, json.decoder.JSONDecodeError):  # Corrupt file
            return "", ""
    else:
        try:
            _file = read_xml_as_dict(filename)
            pre = "@"
            version = 1
        except xml.parsers.expat.ExpatError:  # Corrupt file
            return "", ""

    build = _file.get("PathOfBuilding", {}).get("Build", {})
    if build != {}:
        name = os.path.splitext(filename)[0]
        # Get the maximum length of a name, trimming it if need be
        name = len(name) > max_filename_width and (name[:max_filename_width] + "..") or name
        # Create a spacer string of the correct length to right justify the class info
        spacer = (min(max_length, max_filename_width) - len(name) + 4) * " "

        # The information on the right. pre is @ for xml's ("@level") and "level" for json's
        # version = build.get(f"{pre}version", "1")
        level = build.get(f"{pre}level", "1")
        class_name = build.get(f"{pre}className", "Scion")
        ascend_class_name = build.get(f"{pre}ascendClassName", "None")
        _class = ascend_class_name == "None" and class_name or ascend_class_name
        info_text = f" Level {level} {_class} (v{version})"

        colour = ColourCodes[class_name.upper()].value
        if html:
            if menu:
                return (
                    f'<pre>{name}{spacer}<span style="color:{colour};">{info_text}</span></pre>',
                    class_name,
                )
            else:
                return (
                    f'<pre style="color:{settings.qss_default_text};">{name}{spacer}<span style="color:{colour};">{info_text}</span></pre>',
                    class_name,
                )
        else:
            return f"{name}{spacer}{info_text}", class_name
    else:
        return "", ""


# def json_to_et(json_content):
#     """
#     Convert a json string into a ET.ElementTree
#     :param json_content: String: the json content
#     :return: xml.etree.ElementTree
#     """
#     # convert via a dictionary
#     _dict = json.loads(json_content)
#     xml_content = xmltodict.unparse(_dict, pretty=True)
#     return ET.ElementTree(ET.fromstring(xml_content))


def read_json(filename):
    """
    Reads a json file
    :param filename: Name of xml to be read
    :returns: A dictionary of the contents of the file
    """
    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r", -1, "utf-8") as json_file:
                _dict = json.load(json_file)
                return _dict
        # parent of IOError, OSError *and* WindowsError where available
        except EnvironmentError:
            print(f"Unable to open {_fn}")
    return None


def read_json16(filename):
    """
    Reads a json file
    :param filename: Name of xml to be read
    :returns: A dictionary of the contents of the file
    """
    _fn = Path(filename)
    if _fn.exists():
        try:
            with _fn.open("r", encoding="utf-16") as json_file:
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
        with _fn.open("w", -1, "utf-8") as json_file:
            json.dump(_dict, json_file, indent=2)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        print(f"Unable to write to {_fn}")


def read_xml_as_dict(filename):
    """
    Reads a XML file
    !!!! This stays in this module as it is used by get_file_info !!!!
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


# # Why don't these work ?
# def dump_class_to_text(filename, _class):
#     with open(filename, "a") as f_out:
#         pprint(
#             dict(
#                 (name, getattr(_class, name))
#                 for name in dir(_class)
#                 if not name.startswith("__")
#             ),
#             f_out,
#         )
#
# # Why don't these work ?
# def dump_dict_to_text(filename, _dict):
#     with open(filename, "a") as f_out:
#         print(_dict, f_out)
