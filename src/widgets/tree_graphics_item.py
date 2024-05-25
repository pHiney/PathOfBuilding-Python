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
        self.node_stats = ""
        self.node_recipe = ""
        self.node_reminder = ""
        self.node_isoverlay = False  # If this is an overlay, then the search ring needs to be bigger
        self.node_classStartIndex = -1
        self.node_isAscendancyStart = False
        if node is not None:
            self.node_id = node.id
            self.node_name = node.name
            self.node_stats = node.stats
            self.node_recipe = node.recipe
            self.node_reminder = node.reminderText
            self.node_classStartIndex = node.classStartIndex
            self.node_isAscendancyStart = node.isAscendancyStart

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
        self.setToolTip(self.build_tooltip())

    def build_tooltip(self, mastery_id=0):
        """
        Build a tooltip from the node information and damage data (later).

        :param: mastery_id: if none 0, add mastery stats.
        :return: str: the tooltip
        """
        # if self.node:
        #     print(f"TreeGraphicsItem.build_tooltip: {self.node.type=}, {self.node_name=}, {self.name=}, {self.node.masteryEffects=}")
        if self.item:
            return self.item.tooltip()

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
        if self.node_stats != "":
            stats = ""
            for line in self.node.stats:
                # This was tough. HTML lines break after a -, unless there is a punctuation mark next to it.
                #   '.-.' is an example of what works.
                # Ended up searching for invisble characters: https://www.quora.com/How-do-you-insert-an-invisible-character-in-HTML
                stats += f"{line.replace('-', '&#8205;-&#8205;')}{nl}"
            if stats:
                tool_tip += f'<tr><td><pre>{html_colour_text(self.settings.qss_default_text, stats.rstrip(f"{nl}"))}</pre></td></tr>'
        tool_tip += self.node_reminder and f"<tr><td><pre>{self.node_reminder}</pre></td></tr>" or ""
        tool_tip += f"</table>"
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
