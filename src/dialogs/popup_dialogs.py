"""
simple popups that don't need complex activities to load or execute them
"""

from copy import deepcopy
import base64
import re
import requests

from PySide6.QtCore import Slot, Qt, QSize
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QHBoxLayout,
    QStyleOptionViewItem,
    QVBoxLayout,
)

from PoB.constants import ColourCodes, _VERSION_str, get_http_headers, tree_versions
from PoB.utils import html_colour_text
from widgets.ui_utils import HTMLDelegate

from ui.PoB_Main_Window import Ui_MainWindow


def yes_no_dialog(win, title, text):
    """Return true if the user selects Yes."""
    return QMessageBox.question(win, title, text, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes


def ok_dialog(win, title, text, btn_text="OK"):
    """Notify the user of some information."""
    dlg = QMessageBox(win)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    dlg.addButton(btn_text, QMessageBox.YesRole)
    dlg.setIcon(QMessageBox.Information)
    dlg.exec_()


def critical_dialog(win, title, text, btn_text="Close"):
    """Notify the user of some critical? information."""
    dlg = QMessageBox(win)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    dlg.addButton(btn_text, QMessageBox.YesRole)
    dlg.setIcon(QMessageBox.Critical)
    dlg.exec_()


"""######## MasteryPopup. Choose a mastery from the passed in Node ########"""


class MasteryPopup(QDialog):
    def __init__(self, tr, node, current_spec, mastery_effects_nodes, _win: Ui_MainWindow = None):
        """
        Choose a mastery from the passed in Node.

        :param tr: App translate function
        :param node: node(): this mastery node
        :param current_spec: Spec(): the current Spec class for looking up assigned effects
        :param mastery_effects_nodes: list: list of node ids in this mastery group
        """
        super().__init__(_win)

        self.id = node.id
        self.node_effects = node.masteryEffects  # Dict [id] = [stats]
        self.selected_effect = -1
        self.selected_row = -1
        self.starting = True

        assigned_effects = {}
        # turn mastery_effects_nodes into a dict indexed by effect, *IF* it is assigned elsewhere
        for _id in mastery_effects_nodes:
            effect = current_spec.get_mastery_effect(_id)
            if effect > 0:
                assigned_effects[effect] = _id

        # Fill list box with effects' name
        self.listbox = QListWidget()
        for idx, (e_id, effect) in enumerate(self.node_effects.items()):
            item = QListWidgetItem()
            item.setData(20, e_id)
            tooltip = effect.get("reminderText", "")
            stats = " ".join(effect["stats"])
            effects_assigned_node = assigned_effects.get(e_id, -1)
            # if effect is assigned elsewhere, make it unselectable. Make this node's effect green if it's assigned.
            match effects_assigned_node:
                case -1:
                    # unassigned
                    item.setText(html_colour_text("WHITE", stats))
                    preamble = "Unassigned"
                case node.id:
                    # assigned to this node
                    item.setText(html_colour_text("GREEN", stats))
                    preamble = "Currently Assigned"
                    self.selected_row = idx
                    self.selected_effect = e_id
                case _:
                    # assigned to another node
                    item.setFlags(Qt.NoItemFlags)
                    item.setText(html_colour_text("RED", stats))
                    preamble = "Already Assigned"
                # strip brackets from reminder.
            tooltip = "  ".join(effect["reminder"]).replace("(", "").replace(")", ";")
            if tooltip:
                item.setToolTip(tr(f"({preamble}),\t{tooltip.rstrip(';')}"))
            else:
                item.setToolTip(tr(f"({preamble})"))
            self.listbox.addItem(item)

        # Allow us to print in colour.
        delegate = HTMLDelegate(self)
        delegate._list = self.listbox
        self.listbox.setItemDelegate(delegate)
        size = delegate.sizeHint(0, 0)
        self.listbox.setMinimumWidth(size.width() + 40)
        self.listbox.setMaximumHeight(size.height() * len(self.node_effects) + 20)

        self.setWindowTitle(node.name)
        self.setWindowIcon(node.active_image.pixmap())

        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Double Click to select an effect."))
        self.layout.addWidget(self.listbox)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

        self.listbox.setCurrentRow(self.selected_row)
        if self.selected_row < 0:
            self.listbox.clearSelection()
        self.listbox.itemDoubleClicked.connect(self.effect_selected)
        self.listbox.currentRowChanged.connect(self.effect_row_changed)

    @Slot()
    def effect_selected(self, current_item):
        """

        :param: current_item: QListWidgetItem: the selected item. Not used
        :return: N/A
        """
        self.selected_effect = current_item.data(20)
        # print("effect_selected: item, row, effect", QListWidgetItem(current_item).data(20), current_row, effect)
        self.accept()

    def effect_row_changed(self, current_row):
        """
        Turn off the first selection. On first show, the listwidget will select the first row. We don't want that.

        :param: current_row: int: the selected row. -1 for no selection.
        :return: N/A
        """
        if current_row < 0:
            return
        # Protect against the first row selection
        if self.starting:
            self.starting = False
            self.listbox.setCurrentRow(-1)


"""######## ImportTreePopup. Import a passive Tree URL ########"""


class ImportTreePopup(QDialog):
    def __init__(self, tr, curr_tree_name: str = "", _win: Ui_MainWindow = None):
        """
        Initialize
        :param tr: App translate function
        """
        super().__init__(_win)
        self.spec_name = curr_tree_name
        if curr_tree_name == "":
            self.setWindowTitle(tr(f"Import tree from URL to a new tree."))
            self.intro_text = tr(f"Enter passive tree URL.")
        else:
            self.setWindowTitle(tr(f'Import tree from URL, overwriting "{self.spec_name}".'))
            self.intro_text = tr(f'Enter passive tree URL, overwriting "{self.spec_name}".')
        self.seems_legit_text = tr(html_colour_text("GREEN", "Seems valid. Lets go."))
        self.not_valid_text = tr(html_colour_text("RED", "Not valid. Try again."))
        self.setWindowIcon(QIcon(":/Art/Icons/paper-plane-return.png"))
        self.decoded_state: bool = False

        self.label_url = QLabel(self.intro_text)
        self.lineedit_url = QLineEdit()
        self.lineedit_url.setMinimumWidth(600)
        self.lineedit_url.textChanged.connect(self.validate_url)

        self.label_name = QLabel("New tree's name.")
        self.lineedit_name = QLineEdit()
        self.lineedit_name.setMinimumWidth(600)
        self.lineedit_name.textChanged.connect(self.validate_import_button_visibility)
        self.label_name.setVisible(curr_tree_name == "")
        self.lineedit_name.setVisible(curr_tree_name == "")

        self.btn_import = QPushButton("Import")
        self.btn_import.setEnabled(False)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        self.button_box.addButton(self.btn_import, QDialogButtonBox.AcceptRole)
        self.button_box.setCenterButtons(True)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label_url)
        self.layout.addWidget(self.lineedit_url)
        self.layout.addWidget(self.label_name)
        self.layout.addWidget(self.lineedit_name)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def check_for_character_name_in_url(self, url_parts):
        """
         Check for the following variables in the url: accountName=xyllywyt&characterName=PrettyXylly
         Update the name linedit if eitehr or both of these are found. Ignore any others.
        :param url_parts:
        :return: N/A
        """
        # print("check_for_character_name_in_url", len(url_parts))
        if url_parts and len(url_parts) > 1:
            account, character = "", ""
            for var in url_parts[1].split("&"):
                opts = var.split("=")
                if opts:
                    match opts[0]:
                        case "accountName":
                            account = opts[1]
                            self.lineedit_name.setText(account)
                        case "characterName":
                            character = opts[1]
                            self.lineedit_name.setText(character)

            if account and character:
                self.lineedit_name.setText(f"{character}, imported from {account}")

    @Slot()
    def validate_url(self, text):
        """
        Validate the lineedit input (url hopefully). Turn on/off the import button and change label text as needed.

        :param text: str: the current text of the line edit.
        :return: N/A
        """
        if text == "":
            self.label_url.setText(self.intro_text)
        else:
            # check the validity of what was passed in
            ggg = re.search(r"http.*passive-skill-tree/(.*/)?(.*)", text)
            poep = re.search(r"http.*poeplanner.com/(.*)?(.*)", text)
            if ggg is not None:
                # ggg.group(1) would be the version if present
                # ggg.group(2) is the encoded string and variables (accountName= & characterName=) if present
                # url_parts[0] will be the encoded string and the rest will be variable=value&...
                url_parts = ggg.group(2).split("?")
                decoded_bytes = base64.urlsafe_b64decode(url_parts[0] + "==")
                self.decoded_state = len(decoded_bytes) > 7
                self.validate_import_button_visibility(self.spec_name)
                if self.decoded_state:
                    self.check_for_character_name_in_url(url_parts)
                    self.label_url.setText(self.seems_legit_text)
            elif poep is not None:
                # ggg.group(1) is the encoded string and variables if present, (probably not required for poeplanner)
                # url_parts[0] will be the encoded string and the rest will be variable=value&...
                url_parts = poep.group(1).split("?")
                decoded_bytes = base64.urlsafe_b64decode(url_parts[0] + "==")
                self.decoded_state = len(decoded_bytes) > 15
                if self.decoded_state:
                    self.validate_import_button_visibility(self.spec_name)
                    self.label_url.setText(self.seems_legit_text + " Tree nodes and Bandits info only. Cluster nodes won't show.")
            else:
                self.btn_import.setEnabled(False)
                self.label_url.setText(self.not_valid_text)

    @Slot()
    def validate_import_button_visibility(self, text):
        """
        Update the spec name lineedit input. Turn on/off the import button and change label text as needed.

        :param text: str: the current text of the line edit.
        :return: N/A
        """
        print(f"validate_import_button_visibility: text: '{text}' : ", type(text))
        print(f'validate_import_button_visibility: decoded_state: "{self.decoded_state}" : ', type(self.decoded_state))
        self.spec_name = text
        self.btn_import.setEnabled(self.decoded_state and (self.lineedit_name.isHidden() or text != ""))


"""######## ExportTreePopup. Export a passive Tree URL ########"""


class ExportTreePopup(QDialog):
    def __init__(self, tr, url, _win: Ui_MainWindow = None):
        """
        Initialize
        :param tr: App translate function
        :param url: str: the encoded url
        :param _win: MainWindow(): reference for accessing the statusbar
        """
        super().__init__()
        self.tr = tr
        self.win = _win
        self.intro_text = tr("Passive tree URL.")
        self.shrink_text = f'{tr("Shrink with")} PoEURL'
        self.setWindowTitle(tr("Export tree to URL"))
        self.setWindowIcon(QIcon(":/Art/Icons/paper-plane.png"))

        self.label_url = QLabel(self.intro_text)
        self.lineedit_url = QLineEdit()
        self.lineedit_url.setMinimumWidth(600)
        self.lineedit_url.setText(url)

        self.btn_copy = QPushButton(tr("Copy"))
        self.btn_copy.setAutoDefault(False)
        self.btn_copy.clicked.connect(self.copy_url)
        self.btn_shrink = QPushButton(self.shrink_text)
        self.btn_shrink.clicked.connect(self.shrink_url)
        self.btn_shrink.setAutoDefault(False)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        self.button_box.addButton(self.btn_shrink, QDialogButtonBox.ActionRole)
        self.button_box.addButton(self.btn_copy, QDialogButtonBox.ActionRole)
        self.button_box.setCenterButtons(True)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label_url)
        self.layout.addWidget(self.lineedit_url)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        self.set_lineedit_selection()

    def set_lineedit_selection(self):
        """Ensure linedit has focus and the text selected"""
        self.lineedit_url.setFocus(Qt.OtherFocusReason)
        self.lineedit_url.setSelection(0, len(self.lineedit_url.text()))

    def copy_url(self):
        """Copy the text in the lineedit to the clipboard"""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.lineedit_url.text())
        self.set_lineedit_selection()

    def shrink_url(self):
        """Call poeurl and get the url 'shrinked'"""
        self.btn_shrink.setText(f'{self.tr("Shrinking")} ...')
        self.btn_shrink.setEnabled(False)
        url = f"http://poeurl.com/shrink.php?url={self.lineedit_url.text()}"
        response = None
        try:
            response = requests.get(url, headers=get_http_headers, timeout=6.0)
            url = f'http://poeurl.com/{response.content.decode("utf-8")}'
            self.lineedit_url.setText(url)
            self.lineedit_url.setSelection(0, len(url))
            self.btn_shrink.setText(self.tr("Done"))
        except requests.RequestException as e:
            self.win.update_status_bar(f"Error retrieving 'Data': {response.reason} ({response.status_code}).")
            self.btn_shrink.setEnabled(True)
            self.btn_shrink.setText(self.shrink_text)
            print(f"Error accessing 'http://poeurl.com': {e}.")
        self.set_lineedit_selection()


"""######## NewTreePopup. Export a passive Tree URL ########"""


class NewTreePopup(QDialog):
    def __init__(self, tr, _win: Ui_MainWindow = None):
        """
        Initialize
        :param tr: App translate function
        """
        super().__init__(_win)
        # self.intro_text = tr("New passive tree.")
        self.setWindowTitle(tr("New passive tree"))
        self.setWindowIcon(QIcon(":/Art/Icons/tree--pencil.png"))

        # self.label = QLabel(self.intro_text)
        self.lineedit_name = QLineEdit()
        self.lineedit_name.setMinimumWidth(400)
        self.lineedit_name.setPlaceholderText("New tree, Rename Me")
        # self.lineedit_name.textChanged.connect(self.validate_url)
        self.combo_tree_version = QComboBox()
        for ver in tree_versions.keys():
            self.combo_tree_version.addItem(tree_versions[ver], ver)
        self.combo_tree_version.setCurrentIndex(len(tree_versions) - 1)

        self.btn_exit = QPushButton("Don't Save")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        self.button_box.addButton(self.btn_exit, QDialogButtonBox.RejectRole)
        self.button_box.setCenterButtons(True)

        self.hlayout = QHBoxLayout()
        # self.hlayout.addWidget(self.label)
        self.hlayout.addWidget(self.lineedit_name)
        self.hlayout.addWidget(self.combo_tree_version)

        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addWidget(self.button_box)
        self.setLayout(self.vlayout)


class LineEditPopup(QDialog):
    def __init__(self, tr, title, _win: Ui_MainWindow = None):
        """
        Initialize
        :param tr: App translate function
        """
        super().__init__(_win)
        # self.intro_text = tr(title)
        self.setWindowTitle(tr(title))
        self.setWindowIcon(QIcon(":/Art/Icons/edit-list-order.png"))

        self.lineedit_name = QLineEdit()
        self.lineedit_name.setMinimumWidth(400)
        self.lineedit_name.setPlaceholderText("I'm empty, type in me ...")

        self.btn_exit = QPushButton("Don't Save")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        self.button_box.addButton(self.btn_exit, QDialogButtonBox.RejectRole)
        self.button_box.setCenterButtons(True)

        self.hlayout = QHBoxLayout()
        # self.hlayout.addWidget(self.label)
        self.hlayout.addWidget(self.lineedit_name)

        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addWidget(self.button_box)
        self.setLayout(self.vlayout)

    @property
    def placeholder_text(self):
        """Do nothing, we just need to declare the property"""
        return ""

    @placeholder_text.setter
    def placeholder_text(self, new_text):
        """Do nothing, we just need to declare the property"""
        self.lineedit_name.setPlaceholderText(new_text)
