"""
File Dialog

Open a dialog for Opening or Saving a character.
"""

from copy import deepcopy
from pathlib import Path
import glob
import os
import re

from PySide6.QtWidgets import QDialog, QListWidgetItem, QFileDialog
from PySide6.QtCore import Qt, Slot

from PoB.build import Build
from dialogs.popup_dialogs import yes_no_dialog
from PoB.settings import Settings
from PoB.pob_file import get_file_info
from PoB.utils import html_colour_text

from ui.PoB_Main_Window import Ui_MainWindow
from ui.dlgBrowseFile import Ui_BrowseFile


class BrowseFileDlg(Ui_BrowseFile, QDialog):
    """File dialog"""

    def __init__(self, _settings: Settings, _build: Build, task, _win: Ui_MainWindow = None):
        """
        File dialog init
        :param _build: A pointer to the currently loaded build
        :param _settings: A pointer to the settings
        :param task: str: Either "Open" or "Save"
        :param _win: A pointer to MainWindow
        """
        super().__init__(None)
        self.win = _win
        self.build = _build
        self.settings = _settings
        self.selected_file = ""
        self.triggers_connected = False
        self.save = task == "Save"
        self.open = task == "Open"

        # UI Commands below this one
        self.setupUi(self)
        self.setWindowTitle(f"{self.windowTitle()} - {task}")

        self.btn_Close.clicked.connect(self.close)
        self.btn_CurrDir.clicked.connect(self.change_dir_clicked)
        self.btn_Task.clicked.connect(self.task_button_clicked)
        self.radioBtn_v2.toggled.connect(self.radio_button_selected)
        self.radioBtn_v1.toggled.connect(self.radio_button_selected)
        self.btn_Task.setText(f"&{task}")
        # Hide or Show the Save file components depending on the task.
        # for idx in range(0, self.hLayout_SaveAs.count()):
        #     self.hLayout_SaveAs.itemAt(idx).widget().setHidden(not self.save)

        self.max_filename_width = 100
        self.list_Files.set_delegate()
        if _build.filename:
            path, name = os.path.split(_build.filename)
            self.save_as_text = name
            self.change_dir(path)  # connects triggers
        else:
            self.change_dir(self.settings.build_path)  # connects triggers

    # Overridden function
    def resizeEvent(self, event):
        """
        Work out how many characters can fit in the listbox. One character is 7.3 pixels (ish)
        Width of the four spaces plus the "Level nnn Elementalist (vn)" is 31
        :param event:
        :return: N/A
        """
        self.max_filename_width = int(self.list_Files.width() / 7.3) - 31
        # forcibly refill the list box by calling the only function with trigger controls
        self.change_dir(self.lineEdit_CurrDir.text())
        QDialog.resizeEvent(self, event)

    @property
    def save_as_text(self):
        """Save As label text. Needed so we can have a setter"""
        return self.lineEdit_SaveAs.text()

    @save_as_text.setter
    def save_as_text(self, text):
        """Add to the SaveAs line edit"""
        self.lineEdit_SaveAs.setText(text)

    def connect_triggers(self):
        """Manage the triggers to prevent trigger storms"""
        if self.triggers_connected:
            return
        self.list_Files.itemClicked.connect(self.list_file_clicked)
        self.list_Files.itemDoubleClicked.connect(self.list_file_double_clicked)
        self.lineEdit_CurrDir.textChanged.connect(self.lineedit_currdir_changed)
        self.lineEdit_CurrDir.editingFinished.connect(self.lineedit_currdir_editing_finished)
        self.triggers_connected = True

    def disconnect_triggers(self):
        """Manage the triggers to prevent trigger storms"""
        if not self.triggers_connected:
            return
        self.list_Files.itemClicked.connect(self.list_file_clicked)
        self.list_Files.itemDoubleClicked.disconnect(self.list_file_double_clicked)
        self.lineEdit_CurrDir.textChanged.disconnect(self.lineedit_currdir_changed)
        self.lineEdit_CurrDir.editingFinished.disconnect(self.lineedit_currdir_editing_finished)
        self.triggers_connected = False

    def fill_list_box(self, this_dir):
        """
        Search the current directory and find files and subdirectories.
        Add each to the list box.
        For files, call get_file_info first.

        :param this_dir:
        :return: N/A
        """
        self.list_Files.clear()
        self.lineEdit_CurrDir.setText(this_dir)
        dirs = [name for name in os.listdir(this_dir) if os.path.isdir(os.path.join(this_dir, name))]
        # add in parent directory if we aren't at the top, ie: C:\ or /
        if os.path.dirname(os.getcwd()) != "/":
            self.add_path_to_listbox("..", "..", "", True)
        for name in dirs:
            self.add_path_to_listbox(f"{name}", f"{name}", "", True)

        # files_grabbed = glob.glob("*.xml") + glob.glob("*.json")
        extension = self.radioBtn_v2.isChecked() and "json" or "xml"
        files_grabbed = glob.glob(f"*.{extension}")
        if files_grabbed:
            # Don't use listBox's sort method as it puts the directories at the bottom
            files_grabbed.sort(key=str.casefold)
            # find longest name
            max_length = max([len(s) for s in files_grabbed])
            for filename in files_grabbed:
                text, class_name = get_file_info(self.settings, filename, max_length, self.max_filename_width)
                if text != "":
                    self.add_path_to_listbox(filename, text, class_name, False)

    def add_path_to_listbox(self, filename, _text, class_name, is_dir):
        """
        Add one directory or file to the listbox.
        :param filename: name of file in current directory, no html tags.
        :param _text: The name of the file, class name and versions (with colours).
        :param class_name: The class name (for tooltip colour).
        :param is_dir: True if a directory
        :return: QListWidgetItem: the item added.
        """
        if is_dir:
            lwi = QListWidgetItem(html_colour_text(self.settings.qss_default_text, f"[{_text}]"))
            # If _name is .., then add the parent directory, else the subdirectory
            path = _text == ".." and os.pardir or _text
            _path = os.path.abspath(os.path.join(self.lineEdit_CurrDir.text(), path))
            lwi.setToolTip(f"<nobr>{html_colour_text(self.settings.qss_default_text, _path)}</nobr>")
        else:
            lwi = QListWidgetItem(_text)
            _path = os.path.abspath(os.path.join(self.lineEdit_CurrDir.text(), filename))
            lwi.setToolTip(f"<nobr>{html_colour_text(class_name, filename)}</nobr>")
        info = {
            "filename": filename,
            "path": _path,
            "class_name": class_name,
        }
        lwi.setData(Qt.UserRole, info)
        self.list_Files.addItem(lwi)
        return lwi

    def change_dir(self, new_dir):
        """
        Change directory if the directory exists and will refill the list box.
        May get called during editing of the directory text box is being edited.
        This function is essentially the orchestrator of the Dialog, and is the only function that control the triggers.
        :param new_dir: str: the directory to change to.
        :return: N/A
        """
        # print(f"change_dir {new_dir}")
        self.disconnect_triggers()
        if Path(new_dir).exists():
            os.chdir(new_dir)
            self.lineEdit_CurrDir.setText(str(new_dir))
            self.fill_list_box(new_dir)
        self.list_Files.setFocus()
        # Guarantee that currentItem() is never None.
        self.list_Files.setCurrentRow(0)
        self.connect_triggers()

    @Slot()
    def lineedit_currdir_changed(self, new_dir):
        # print(f"current_dir_changed {new_dir}")
        self.change_dir(new_dir)

    @Slot()
    def lineedit_currdir_editing_finished(self):
        """After the directory text box has finished being edited, change directory."""
        # print("editing_finished", self.lineEdit_CurrDir.text())
        # forcibly refill the list box
        self.change_dir(self.lineEdit_CurrDir.text())

    @Slot()
    def change_dir_clicked(self):
        """the change dir button is selecte, open a directory chooser dialog."""
        new_dir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if new_dir != "":
            self.change_dir(new_dir)

    @Slot()
    def list_file_clicked(self, item: QListWidgetItem):
        """
        Populate the SaveAs text box as files are selected in the list
        :param item: QListWidgetItem. The item selected
        :return: N/A
        """
        # print("list_file_clicked")
        if "[" in item.text():  # is_dir
            return
        else:
            # Clean the toolTip. The toolTip is the only place we can get the cleanest copy of the file name
            self.lineEdit_SaveAs.setText(re.sub("<[^<]+?>", "", item.toolTip()))

    @Slot()
    def list_file_double_clicked(self, item: QListWidgetItem):
        """
        Selecting a file or directory for opening / saving
        :param item: QListWidgetItem. The item selected
        :return: N/A
        """
        # print("list_file_double_clicked")
        info = item.data(Qt.UserRole)
        if "[" in item.text():  # is_dir
            self.change_dir(info["path"])
        else:
            # do something interesting, like return with the information
            self.file_chosen(item)

    @Slot()
    def task_button_clicked(self):
        """
        Selecting a file or directory for opening / saving
        :return: N/A
        """
        # print("task_button_clicked")
        curr_item = self.list_Files.currentItem()
        if curr_item is not None:
            info = curr_item.data(Qt.UserRole)
            # Only change directory on task button being pressed if we are an Open Dialog
            # *OR* is Save Dialog and lineEdit_SaveAs is empty
            # (this is mainly for keyboard usage)
            if self.open and "[" in curr_item.text():  # is_dir
                self.change_dir(info["path"])
                return
            if self.save and "[" in curr_item.text() and self.lineEdit_SaveAs.text() == "":  # is_dir
                self.change_dir(info["path"])
                return
        # do something interesting, like return with the information
        self.file_chosen(curr_item)

    @Slot()
    def radio_button_selected(self, checked: bool):
        self.fill_list_box(self.lineEdit_CurrDir.text())

    def file_chosen(self, curr_item: QListWidgetItem):
        """
        Actions to be taken when the task button is pressed, but not changing directories.
        Changing directories is done by the calling functions.
        :param: curr_item: QListWidgetItem. Passed in from callers. Can't be None for 'open'.
                            Can be None when saving a file without selecting it's name in the gui.
        :return: N/A
        """
        if self.save:
            save_name = self.lineEdit_SaveAs.text()
            # print(f"file_chosen: save: {save_name=}")
            if save_name == "":
                return
            name, extension = os.path.splitext(save_name)
            # extension will be json or xml. No mucking around with allowing weird extensions.
            extension = self.radioBtn_v2.isChecked() and "json" or "xml"
            save_name = os.path.join(self.lineEdit_CurrDir.text(), f"{name}.{extension}")
            if os.path.exists(save_name):
                if not yes_no_dialog(self, "Overwrite file", f"{save_name} exists. Overwrite"):
                    return
            self.selected_file = save_name
            # print(f"file_chosen: save: {self.selected_file=}")
            self.accept()
        if self.open:
            info = curr_item.data(Qt.UserRole)
            # print("file_chosen: open: ", info["path"])
            self.selected_file = info["path"]
            self.accept()

    # @Slot()
    def rename_file(self):
        """"""
        curr_item = self.list_Files.currentItem()
        info = curr_item.data(Qt.UserRole)
        # Don't try to rename the parent directory.
        if curr_item.text() == "[..]":
            old_name = info["name"]
            return
        # Need to know whether to popup a dialog or press F2, like Manage Trees (including it's name bug)
        # os.rename
