"""
TreeItem Class

This class represents a graphical instance of one visual element of a Passive Tree for a given tree version.

"""

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QGuiApplication
from PySide6.QtWidgets import QGraphicsPixmapItem

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
        self.node_tooltip = ""
        self.node_stats = ""
        self.node_name = ""
        self.node_type = ""
        self.node_reminder = ""
        self.node_isoverlay = False  # If this is an overlay, then the search ring needs to be bigger
        self.node_classStartIndex = -1
        self.node_isAscendancyStart = False
        if node is not None:
            self.node_id = node.id
            self.node_stats = node.stats
            if "Socket" not in node.name:
                self.node_name = node.name
            self.node_type = node.type
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

    def build_tooltip(self):
        """
        Build a tooltip from the node information and damage data (later).

        :return: str: the tooltip
        """
        # print(f"TreeGraphicsItem.build_tooltip: {self.node_type=}, {self.name=}, {self.item=}")
        if self.item:
            return self.item.tooltip()

        tool_tip = ""
        if self.node_name:
            if Qt.KeyboardModifier.AltModifier in QGuiApplication.keyboardModifiers():
                tool_tip = f"{self.node_name}, {self.node_id}"
            else:
                tool_tip = f"{self.node_name}"
        tool_tip += self.name and f"<nobr>{self.name}" or ""
        if self.node_stats != "":
            for line in self.node_stats:
                # This was tough. HTML lines break after a -, unless there is a punctuation mark next to it.
                #   '.-.' is an example of what works.
                # Ended up searching for invisble characters: https://www.quora.com/How-do-you-insert-an-invisible-character-in-HTML
                tool_tip += f"\n<nobr>{line.replace('-', '&#8205;-&#8205;')}</nobr>"
        tool_tip += self.node_reminder and f"\n<nobr>{self.node_reminder}" or ""
        if tool_tip:
            return html_colour_text(self.settings.qss_default_text, tool_tip)
        else:
            return ""

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
