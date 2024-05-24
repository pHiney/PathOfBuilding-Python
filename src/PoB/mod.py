"""
A class to encapsulate one mod.
Numeric values default to None so that they can be checked for non use. -1 or 0 could be legitimate values.
"""

import re
import locale

from PoB.constants import ColourCodes
from PoB.utils import _debug, html_colour_text, format_number, print_call_stack, search_stats_for_skill


class Mod:
    def __init__(self, settings, _line, template=False) -> None:
        """
        Initialise defaults
        :param _line: the full line of the mod, including variant stanzas.
        :param template: bool: Do Not do calculations or alter the mods.
        """
        self.settings = settings
        self.template = template
        self.grants_skill = ()
        self.my_variants = []

        # this is the text without {variant}, {crafted}. At this point {range} is still present
        m = re.search(r"({.*})(.*)", _line)
        # All the {variants}, {tags} and such
        self.marks = m and m.group(1) or ""
        self.original_line = m and m.group(2) or _line
        # if m:
        #     print(f"{m.groups()=}")

        # The formatted line with the ranged values filled in, if range is present. Used by calc routines
        self.line = self.original_line

        self.corrupted = self.original_line == "Corrupted"

        # value for managing the range of values. EG: 20-40% of ... _range will be between 0 and 1
        self._range_value = -1
        self.min = 0
        self.max = 0
        self.range_sep = ""
        self.min2 = 0
        self.max2 = 0
        # the actual value of the mod, where valid. EG: if _range is 0.5, then this will be 30%
        self.value = 0
        self.value2 = 0

        self.crafted = "{crafted}" in self.marks
        self.fractured = "{fractured}" in self.marks
        self.tooltip_colour = ColourCodes.MAGIC.value
        if self.crafted:
            self.tooltip_colour = ColourCodes.CRAFTED.value
        elif self.fractured:
            self.tooltip_colour = ColourCodes.FRACTURED.value
        elif self.corrupted:
            self.tooltip_colour = ColourCodes.STRENGTH.value
        # No range? Let's set the tooltip.
        self.tooltip = f"{html_colour_text(self.tooltip_colour, self.original_line)}"

        skill, level = search_stats_for_skill(self.original_line)
        if skill:
            self.grants_skill = (skill, level)

        # check for and keep tag information
        m = re.search(r"({tags:[\w,]+})", self.marks)
        self.tags = m and m.group(1) or ""

        # check for and keep variant information
        m = re.search(r"{variant:([\d,]+)}", self.marks)
        self.my_variants = m and [int(variant) for variant in m.group(1).split(",")] or []

        """ sort out the range, min, max, value and the tooltip, if applicable"""
        # If there is a range, then this will be self.original_line with {0} and/or {1} replacing the range values.
        self.line_unformatted = ""
        # print(f"init 1: {self.line=}, {self.original_line=}")
        m2 = (
            re.search(r"\(([0-9.]+)-([0-9.]+)\)(.*)\(([0-9.]+)-([0-9.]+)\)(.*)", self.original_line)
            or re.search(r"\(([0-9.]+)-([0-9.]+)\)(.*)", self.original_line)
            or re.search(r"([0-9.]+) to ([0-9.]+)", self.original_line)
        )
        if m2:
            if not self.template:
                match len(m2.groups()):
                    case 2:
                        # Adds 1 to 40 Lightning Damage to Attacks
                        # This is not an error, just not a ranged mod
                        # print(f"2: {m2.groups()=}, original_line: {_line}")
                        pass
                    case 3:  # '{range:0.5}+(12-16)% to Fire and Cold Resistances'
                        self.min = float(m2.group(1))
                        self.max = float(m2.group(2))
                        self.line_unformatted = re.sub(r"\([0-9.]+-[0-9.]+\)", "{}", self.original_line)
                    case 6:  # '{range:0.5}Adds (8-13) to (20-30) Physical Damage'
                        self.min = float(m2.group(1))
                        self.max = float(m2.group(2))
                        self.range_sep = m2.group(3)
                        self.min2 = float(m2.group(4))
                        self.max2 = float(m2.group(5))
                        _tmp_str = re.sub(r"\([0-9.]+-[0-9.]+\)", "{0}", self.original_line, count=1)
                        self.line_unformatted = re.sub(r"\([0-9.]+-[0-9.]+\)", "{1}", _tmp_str, count=1)

                # trigger property to update value and tooltip
                m1 = re.search(r"{range:([0-9.]+)}", self.marks)
                self.range_value = m1 and float(m1.group(1)) or 0.5

        # print(f"init 2: {self.line=}, {self.line_unformatted=}, {self.original_line=}")

    @property
    def line_for_save(self, full=False) -> str:
        """
        Return the text formatted for the save
        :param full: bool: Include all the variant text also (used for uniques).
        :return:
        """
        # print(f"line_for_save: {self.range_value=}")
        text = self.marks
        if self.range_value >= 0:
            r = locale.format_string("%.3g", self.range_value)
            if "range" in text:
                text = re.sub(r"{range:[0-9.]+}", rf"{{range:{r}}}", text)
            else:
                text += f"{{range:{r}}}"
        text += self.original_line
        return text

    @property
    def range_value(self) -> float:
        return self._range_value

    @range_value.setter
    def range_value(self, new_range):
        """Set a new range and update value and tooltip"""
        self._range_value = new_range
        self.value = self.min + ((self.max - self.min) * new_range)
        # get the value without the trailing .0, so we don't end up with 40.0% or such.
        fmt = self.value < 10 and "%0.3g" or "%0.5g"
        # put the crafted colour on the value only
        value_str = format_number(self.value, fmt, self.settings)
        # print(f"range_value: {new_range=}, {value_str=}")
        value_colored_str = html_colour_text("CRAFTED", value_str)
        # print(f"range.setter: {self.line=}, {self.line_unformatted=}, {self.original_line=}")
        if self.min2:
            self.value2 = self.min2 + ((self.max2 - self.min2) * new_range)
            value_str2 = format_number(self.value2, fmt, self.settings)
            value_colored_str2 = html_colour_text("CRAFTED", value_str2)
            self.line = self.line_unformatted.format(value_str, value_str2)
            tooltip = self.line_unformatted.format(value_colored_str, value_colored_str2)
        else:
            self.line = self.line_unformatted.format(value_str)
            tooltip = self.line_unformatted.format(value_colored_str)
        # colour the whole tip
        self.tooltip = f"{html_colour_text(self.tooltip_colour, tooltip)}"
        # print(f"range.setter: {self.line=}, {self.tooltip=}")
