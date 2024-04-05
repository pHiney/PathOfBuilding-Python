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
from PoB.utils import _debug, print_call_stack


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
        _file = read_json(filename)
        pre = ""
        version = 2
    else:
        _file = read_xml_as_dict(filename)
        pre = "@"
        version = 1

    if _file is None:
        return "", ""

    build = _file.get("PathOfBuilding", {}).get("Build", {})
    if build != {}:
        try:
            filename = Path(filename).relative_to(settings.build_path)
        except ValueError:
            # MainWindow() passes in full path's from the recent_builds settings elements, so no error.
            # but File Open/Save dialog only passes in filenames. This is what gives the ValueError.
            pass
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
        except (EnvironmentError, json.decoder.JSONDecodeError):
            print(f"Unable to open {_fn} (read_json)")
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
            print(f"Unable to open {_fn} (read_json16)")
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


"""!!!! read_xml_as_dict stays in this module as it is used by get_file_info !!!!. Peter, this means YOU !!!"""


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
        except (EnvironmentError, xml.parsers.expat.ExpatError):
            print(f"Unable to open {_fn} (read_xml_as_dict)")
    return None
