"""
Utilities for the UI that do not have dependencies on MainWindow
"""

from copy import deepcopy
import re

from PySide6.QtCore import Qt, QMargins, QPoint, QRect, QSize
from PySide6.QtGui import QAbstractTextDocumentLayout, QPalette, QTextDocument
from PySide6.QtWidgets import QApplication, QComboBox, QProxyStyle, QStyle, QStyleOptionViewItem, QStyledItemDelegate


def search_stats_list_for_regex(stat_list, regex, default_value, debug=False) -> list:
    """
    Standardise the regex searching of stats
    :param stat_list: list of stats that should match the regex.
    :param regex: the regex.
    :param default_value: int: A value that suits the calculation if no stats found (EG: 1 for multiplication, 0 for addition).
    :param debug: bool: Ease of printing facts for a given specification.
    :return: list: the list of values of the digits. Some results need to be sum'd and others product'd.
    """
    value = []
    for stat in stat_list:
        m = re.search(regex, stat)
        # print(f"{stat=}, {regex=}")
        if m:
            if debug:
                print(f"{stat=}, {regex=}, {value=}, {m=}")
            value.append(int(m.group(1)))
    return value == [] and [int(default_value)] or value


def set_combo_index_by_data(_combo: QComboBox, _data, debug=False) -> int:
    """
    Set a combo box current index based on it's data field.

    :param _combo: the combo box.
    :param _data: the data. There is no type to this, so the passed in type should match what the combo has.
    :param debug: bool. Show more info
    :return: int: the index of the combobox or -1 if not found.
    """
    if _data is None:
        _data = "None"
    # print_call_stack()
    if debug:
        print(f"{_combo.objectName()}: {_data=}, {type(_data)=}")
    index = _combo.findData(_data)
    if index >= 0:
        if debug:
            print(f"Found: {_data=}, {index=}")
        _combo.setCurrentIndex(index)
    return index


def set_combo_index_by_text(_combo: QComboBox, _text, debug=False) -> int:
    """
    Set a combo box current index based on it's text field.

    :param _combo: the combo box.
    :param _text: string: the text.
    :param debug: bool. Show more info
    :return: int: the index of the combobox or -1 if not found.
    """
    if _text is None:
        _text = "None"
    # print_call_stack()
    index = _combo.findText(_text)
    if index >= 0:
        if debug:
            print(f"Found: {_text=}, {index=}")
        _combo.setCurrentIndex(index)
    return index


# https://stackoverflow.com/questions/1956542/how-to-make-item-view-render-rich-html-text-in-qt
class HTMLDelegate(QStyledItemDelegate):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        # the list of WidgetItems from a QListView
        self._list = None
        self.doc = QTextDocument()

    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        style = QApplication.style() if options.widget is None else options.widget.style()

        doc = QTextDocument(self.parent())
        doc.setHtml(options.text)

        options.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, options, painter)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, options)
        painter.save()
        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    """ PSH: 20240427 Commented out to suit QComboBox testing. Noted ListViews seemed to still work """

    def sizeHint(self, option, index):
        """Inherited function to return the max width of all text items"""
        if type(index) is int:
            # print("HTMLDelegate.sizeHint", self._list.objectName(), index)
            self.doc.setHtml(self._list.item(index).text())
        else:
            # print("HTMLDelegate.sizeHint", self._list.objectName(), index.row())
            self.doc.setHtml(self._list.item(index.row()).text())
        return QSize(self.doc.idealWidth() + 20, self.doc.size().height())
