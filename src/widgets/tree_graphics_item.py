"""
TreeItem Class

This class represents a graphical instance of one visual element of a Passive Tree for a given tree version.

"""

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QGuiApplication
from PySide6.QtWidgets import QGraphicsPixmapItem

from PoB.constants import ColourCodes
from PoB.settings import Settings
from PoB.utils import html_colour_text


class TreeGraphicsItem(QGraphicsPixmapItem):
    def __init__(self, _settings: Settings, _image: str, node, z_value=0, selectable=False) -> None:
        super(TreeGraphicsItem, self).__init__()
        self.settings = _settings
        self.win = self.settings._win
        self.name = ""
        self.filename = ""
        self.tool_tip = ""
        self.data = ""
        self.setPixmap(_image)
        if not type(_image) is QPixmap:
            self.filename = str(_image)
        self.width = self.pixmap().size().width()
        self.height = self.pixmap().size().height()
        self._z_value = z_value
        self.layer = z_value

        # ToDo: Do we need selectable ?
        # self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.selectable = selectable

        # these are to have a fast way for a graphic item to identify its owner node's params. Used by mouse events
        # Maybe have just the node reference ?
        self.node = node
        self.node_id = 0
        self.node_name = ""
        self.node_type = ""
        self.node_stats = ""
        self.node_recipe = ""
        self.node_reminder = ""
        self.node_mastery_effects = {}
        self.node_isoverlay = False  # If this is an overlay, then the search ring needs to be bigger
        self.node_classStartIndex = -1
        self.node_isAscendancyStart = False
        if node is not None:
            self.node_id = node.id
            self.node_name = node.name
            self.node_type = node.type
            self.node_stats = node.stats
            self.node_recipe = node.recipe
            self.node_reminder = node.reminderText
            self.node_classStartIndex = node.classStartIndex
            self.node_isAscendancyStart = node.isAscendancyStart
            self.node_mastery_effects = node.masteryEffects

        self._item = None  # reference to a Jewel, if this is a socket

    @property
    def layer(self):
        return self._z_value

    @layer.setter
    def layer(self, z_value):
        self._z_value = z_value
        self.setZValue(z_value)

    @property
    def selectable(self):
        return False

    @selectable.setter
    def selectable(self, selectable):
        self.setAcceptTouchEvents(selectable)
        self.setAcceptHoverEvents(selectable)

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, new_item):
        self._item = new_item
        self.name = new_item.name

    # Inherited, don't change definition
    def setScale(self, scale: int = 1):
        super(TreeGraphicsItem, self).setScale(scale)
        self.width *= scale
        self.height *= scale

    # Inherited, don't change definition
    def hoverEnterEvent(self, event):
        # print(f"TreeGraphicsItem.hoverEnterEvent: {self.node_type=}, {self.node_name=}, {self.name=}, {self.tool_tip=}")
        # Don't allow Mastery tootip to be rewritten. It is created/set by TreeView(), on assignment of the node.
        if self.node_mastery_effects or self.tool_tip:
            self.setToolTip(self.tool_tip)
            return
        self.setToolTip(self.build_tooltip())

    def build_tooltip(self, mastery_id=0):
        """
        Build a tooltip from the node information and damage data (later).
        Sets self.tool_tip to prevent constant processing. DMG, when ready, can be added to the prebuilt info.

        :param: mastery_id: if none 0, add mastery stats (when called from TreeView).
        :return: str: the tooltip
        """

        def add_array_to_tooltip(stats, colour=self.settings.qss_default_text):
            """

            :param stats: list of strings
            :param colour:
            :return: str: Formatted output if the array contained strings
            """
            text = ""
            if type(stats) is str:
                stats = [stats]
            for line in stats:
                # This was tough. HTML lines break after a -, unless there is a punctuation mark next to it.
                #   '.-.' is an example of what works.
                # Ended up searching for invisble characters: https://www.quora.com/How-do-you-insert-an-invisible-character-in-HTML
                text += f"{line.replace('-', '&#8205;-&#8205;')}{nl}"
            if text != nl:
                return f'<tr><td><pre>{html_colour_text(colour, text.rstrip(f"{nl}"))}</pre></td></tr>'
            else:
                return ""

        # print(f"TreeGraphicsItem.build_tooltip: {self.node_type=}, {self.node_name=}, {self.name=}, {mastery_id=}")
        if self.item:
            return self.item.tooltip()

        # Only rebuild on first time through or when a mastery is chosen
        # print(f"{self.tool_tip=}")
        if self.tool_tip and mastery_id == 0:
            return self.tool_tip

        nl = "\n"
        tool_tip = (
            f"<style>"
            f"table, th, td {{border: 1px solid {ColourCodes.UNIQUE.value}; border-collapse: collapse; vertical-align: middle;}}"
            f"td  {{padding-left:9px; padding-right:9px; text-align: center;}}"
            f"</style>"
            f'<table width="425">'
            f"<tr><th>"
        )
        tool_tip += f"<font size='4' color='white'>{self.node_name and self.node_name or self.name}</font>&nbsp;&nbsp;&nbsp;"
        if self.node_recipe:
            for recipe in self.node_recipe:
                tool_tip += f"&nbsp;&nbsp;&nbsp;{recipe.replace('Oil','')}<img src=':/Art/TreeData/{recipe}.png' width='25' height='25'/>"
        if Qt.KeyboardModifier.AltModifier in QGuiApplication.keyboardModifiers():
            tool_tip += f", {self.node_id}"
        tool_tip += "</th></tr>"
        # Mastery nodes don't have stats, lookup the effect instead
        stats = ""
        reminder = ""
        if mastery_id != 0:
            mastery = self.node_mastery_effects.get(mastery_id, {})
            if mastery:
                stats = mastery.get("stats", ["fred"])
                reminder = mastery.get("reminder", "")
        if self.node_stats:
            stats = self.node_stats
            reminder = self.node_reminder
        # print(f"{stats=}, {reminder=}")
        tool_tip += add_array_to_tooltip(stats)
        tool_tip += add_array_to_tooltip(reminder, "TIP")
        # tool_tip += reminder and f"<tr><td><pre>{reminder}</pre></td></tr>" or ""
        tool_tip += f"</table>"
        self.tool_tip = tool_tip
        # print(f"{tool_tip=}")
        return tool_tip

    # not sure if this is needed
    # def hoverLeaveEvent(self, event):
    #     pass

    # Inherited, don't change definition
    # def mousePressEvent(self, event) -> None:
    #     print(f"TreeGraphicsItem.mousePressEvent: {self.filename}, {self.data}, {self.node_id}")
    #     # AltModifier (altKey), ControlModifier(crtlKey)
    #     event.accept()

    # Inherited, don't change definition
    # def mouseReleaseEvent(self, event) -> None:
    #     print(f"TreeGraphicsItem.mouseReleaseEvent: {self.filename}, {self.node_id}")
    #     # AltModifier (altKey), ControlModifier(crtlKey)
    #     event.accept()
