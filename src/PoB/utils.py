"""
Utilities for the app that do not have dependencies on the UI/PySide
"""

import base64
from copy import deepcopy
import datetime
import itertools
import operator
import re
import traceback
import zlib

from PoB.constants import ColourCodes, pob_debug, locale


class PoBDict(object):
    """
    Turns a dictionary into a class. We use load and save to ensure there is only one instatiation of the class
    thoughout the life of the application. This makes it easier to share between other classes.
    If descendant's want to have variables that are not saved in the dictionary, they need to be prefixed with '_'.
      EG: self._variable1 = "blah"
    """

    def __init__(self, dictionary):
        """PoBDict. Constructor"""
        self.load(dictionary)

    def __repr__(self):
        """return: str:"""
        return "%s" % self.__dict__

    def delete(self, key):
        """Error safe del"""
        if self.exists(key):
            delattr(self, key)

    def load(self, dictionary=None):
        """Reset internal dictionary attr's"""
        # Only need to delete the top level as GC should dispose of the rest.
        # On first run through, keys() is empty.
        keys = [key for key in self.__dict__.keys() if not key.startswith("_")]
        # print(f"PoBdict: load: {keys=}")
        for key in keys:
            delattr(self, key)

        if dictionary:
            for key, value in dictionary.items():
                if type(value) is dict:
                    setattr(self, key, PoBDict(value))
                else:
                    setattr(self, key, value)

    def save(self):
        """return: dict: the python type dictionary representation of the class"""
        _dict = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if type(value) is PoBDict:
                    _dict[key] = value.save()
                else:
                    _dict[key] = value
        return _dict

    def exists(self, key):
        """Does key exist ?"""
        return getattr(self, key, None) is not None

    def new_child(self, key):
        if not self.exists(key):
            setattr(self, key, PoBDict({}))

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()


def str_to_bool(in_str):
    """
    Return a boolean from a string. As the settings could be manipulated by a human, we can't trust eval()
      EG: eval('os.system(`rm -rf /`)')
    :param: in_str: String: The setting to be evaluated
    :returns: True if it looks like it could be true, otherwise False
    """
    return in_str.lower() in ("yes", "true", "t", "1", "on")


def bool_to_str(in_bool):
    """
    Return a string from a boolean.
    :param: in_bool: Boolean: The setting to be evaluated
    :returns: String: true or false
    """
    return in_bool and "true" or "false"


is_str_a_boolean = str_to_bool


def is_str_a_number(in_str):
    """
    Check if this string is a number
    :param: in_str: String: The setting to be evaluated
    :returns: True if it looks like it could be afloat or integer
    """
    return in_str.startswith("-") and in_str[1:].isdigit() or in_str.isdigit()


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


def print_call_stack(full=False, idx=-3):
    """
    Ahh debug. It's wonderful
    :param: full: Bool: True if you want the full stack trace,
            elsewise just print the parent of the function that called this
    :return: N/A
    """
    lines = traceback.format_stack()
    if full:
        for line in lines[:-2]:
            print(line.strip())
    else:
        print(lines[idx].strip())
    print("------\n")


def _debug(*text):
    """
    print a debug line if debug is enabled
    :param: text: list. The info to print
    :return: N/A
    """
    if pob_debug:
        lines = traceback.format_stack()
        print(f"{datetime.datetime.now()}: {text}", ":", lines[-2].strip().partition("\n")[0])


def unique_sorted(values):
    """Return a sorted list of the given values, without duplicates."""
    return map(operator.itemgetter(0), itertools.groupby(sorted(values)))


def decode_base64_and_inflate(byte_array):
    """
    Decode a byte array and then zlib inflate it to make real characters
    :param byte_array: an array like you get fro downloading from pastebin or pobb.in
    :return: a string of real characters
    """
    try:
        decoded_data = base64.urlsafe_b64decode(byte_array)
        return zlib.decompress(decoded_data, 0)
    except:
        return None


def deflate_and_base64_encode(string_val):
    """
    zlib compress a string of characters and base64 encoded them
    :param string_val: a string or real characters
    :return: a byte array or the compressed and encoded string_val
    """
    # try:
    zlibbed_str = zlib.compress(string_val)
    return base64.urlsafe_b64encode(zlibbed_str)
    # except:
    #     return None


def html_colour_text(colour, text):
    """
    Put text into html span tags.

    :param colour: string: the #xxxxxx colour to be used or ColourCodes name.
    :param text: the text to be coloured.
    :return: str: html colour coded text.
    """
    if colour[0] == "#":
        c = colour
    else:
        c = ColourCodes[colour.upper()].value
    newline = "\n"
    return f'<span style="color:{c};">{text.replace(newline,"<BR>")}</span>'


def format_number(the_number, format_str, settings, pos_neg_colour=False):
    """
    Locale aware number formatting
    :param the_number: int or float.
    :param format_str: str: A format string : like '%10.2f' or '%d'
    :param settings: Settings(). So we can access the colours and show_thousands_separators
    :param pos_neg_colour: bool. Whether to colour the return value
    :return: str: String represntation of the number, formatted as needed.
    """
    # if format is an int, force the value to be an int.
    if "d" in format_str:
        the_number = round(the_number)  # locale.format_string will round 99.5 or 99.6 to 99 using a %d format_str (truncates).
    show_thousands_separators = settings is None and False or settings.show_thousands_separators
    return_str = locale.format_string(format_str, the_number, grouping=show_thousands_separators)
    if pos_neg_colour:
        colour = the_number < 0 and settings.colour_negative or settings.colour_positive
        return_str = html_colour_text(colour, return_str)
    return return_str


def search_list_for_regex(_list, regex, debug=False) -> list:
    """
    Standardise the regex searching of stats.
    :param _list: list of stats that should match the regex.
    :param regex: the regex.
    :param debug: bool: Ease of printing facts for a given specification.
    :return: list: the list of values that match the regex.
    """
    return [line for line in _list if re.search(regex, line)]


def search_stats_for_skill(stats, debug=False):
    """
    Check for 'Trigger Level nn Skill' or 'Grants Level nn Skill'
    :param stats: str or list of str:
    :param debug: bool:
    :return: set: ("skill name", int("skill level"))
    """
    skill, level = "", 0
    if type(stats) is list:
        stats = " ".join(stats)
    g = re.search(r"Grants Level (\d+) (.*) Skill", stats)
    t = re.search(r"Trigger Level (\d+) (.*) when", stats)
    if debug:
        print(f"search_stats_for_skill, {stats=}, {g=}, {t=}")
    if g:
        skill, level = (g.group(2), int(g.group(1)))
    if t:
        skill, level = (t.group(2), int(t.group(1)))

    return skill, level


def list_to_str(_input_list):
    if type(_input_list) is list:
        return "\n".join(_input_list)
    else:
        return ""


def str_to_list(_input_str):
    if type(_input_str) is str:
        return [y for y in (x.strip(" \t\r\n") for x in _input_str.splitlines()) if y]
    else:
        return []
