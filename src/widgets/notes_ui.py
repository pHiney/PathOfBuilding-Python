"""
This Class manages all the elements and owns some elements of the "NOTES" tab
"""

from copy import deepcopy
import re

from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QBrush

from PoB.constants import ColourCodes, colourEscapes
from PoB.settings import Settings

from ui.PoB_Main_Window import Ui_MainWindow


class NotesUI:
    def __init__(self, _settings: Settings, _win: Ui_MainWindow) -> None:
        self.settings = _settings
        self.win = _win
        self.modified = False
        self.notes = self.notes_html = ""

        # Add content to Colour ComboBox
        self.win.combo_Notes_Colour.addItems([colour.name.title() for colour in ColourCodes])
        for index in range(self.win.combo_Notes_Colour.count()):
            colour = ColourCodes[self.win.combo_Notes_Colour.itemText(index).upper()].value
            self.win.combo_Notes_Colour.setItemData(index, QBrush(colour), Qt.ForegroundRole)

        self.win.btn_ConvertToHTML.setVisible(False)
        self.win.btn_ConvertToHTML.clicked.connect(self.convert_to_html)
        self.win.combo_Notes_Font.currentFontChanged.connect(self.set_notes_font)
        self.win.spin_Notes_FontSize.valueChanged.connect(self.set_notes_font_size)
        self.win.combo_Notes_Colour.currentTextChanged.connect(self.set_notes_font_colour)

    def load(self, _notes, _notes_html):
        """
        Load internal structures from the build object
        If there are no HTML notes, then get the Text based ones

        :param _notes_html: String: HTML version of notes. Is None if not in the source XML
        :param _notes: String: Plain text version of notes
        :return: N/A
        """
        # print(f"Notes.load: {_notes=}\n\n\n{_notes_html=}")
        self.notes = _notes
        self.notes_html = _notes_html
        if _notes_html:
            self.win.btn_ConvertToHTML.setVisible("^7" in _notes_html)
            self.win.textedit_Notes.setHtml(_notes_html)
        else:
            if _notes:
                self.win.btn_ConvertToHTML.setVisible(True)
                # self.win.textedit_Notes.setPlainText(_notes.strip())
                self.win.textedit_Notes.setPlainText(_notes)

    def save(self):
        """
        Save internal structures back to the build object

        :return: two strings representing the plain text and the html text
        """
        # print(f"Notes.save: {self.win.textedit_Notes.document().toHtml()=}")
        _notes_html = self.win.textedit_Notes.document().toHtml()
        _notes = self.win.textedit_Notes.document().toPlainText()
        self.modified = False
        return _notes, _notes_html

    def convert_to_html(self):
        """
        Convert the lua colour codes to html and sets the Notes control with the new html text

        :return: N/A
        """
        if self.notes:
            text = self.notes
        elif self.notes_html:
            text = self.notes_html
        else:
            return
        # remove all obvious duplicate colours (mainly ^7^7)
        for idx in range(10):
            while f"^{idx}^{idx}" in text:
                text = text.replace(f"^{idx}^{idx}", f"^{idx}")
        # remove single charactor colours for their full versions
        for idx in range(10):
            while f"^{idx}" in text:
                text = text.replace(f"^{idx}", f"^{colourEscapes[idx].value.replace('#', 'x')}")

        # search for the lua colour codes and replace them with span tags
        m = re.search(r"(\^x[0-9A-Fa-f]{6})", text)
        while m is not None:
            # get the colour from the match
            c = re.search(r"([0-9A-Fa-f]{6})", m.group(1))
            text = text.replace(m.group(1), f'</span><span style="color:#{c.group(1)};">')
            m = re.search(r"(\^x[0-9A-Fa-f]{6})", text)

        # check for a leading closing span tag
        f = re.match("</span>", text)
        if f is not None:
            text = text[7:]
        # check for no leading span tag
        f = re.match("<span ", text)
        if f is None:
            text = f'<span style="color:{ColourCodes.NORMAL.value};">{text}'
        # replace newlines
        text = text.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        self.notes_html = text.replace("\n", "<br>")

        # print(f"{self.notes_html=}")

        self.win.textedit_Notes.setFontPointSize(self.win.spin_Notes_FontSize.value())
        self.win.textedit_Notes.setCurrentFont(self.win.combo_Notes_Font.currentText())
        self.win.textedit_Notes.setHtml(self.notes_html)
        self.win.btn_ConvertToHTML.setVisible(False)
        self.win.textedit_Notes.setFocus()

    # don't use native signal/slot connection, so we can set focus back to edit box
    @Slot()
    def set_notes_font_size(self, _size):
        """
        Actions required for changing the TextEdit font size. Ensure that the TextEdit gets the focus back.

        :return: N/A
        """
        self.win.textedit_Notes.setFontPointSize(_size)
        self.win.textedit_Notes.setFocus()

    # don't use native signal/slot connection, so we can set focus back to edit box
    @Slot()
    def set_notes_font_colour(self, colour_name):
        """
        Actions required for changing TextEdit font colour. Ensure that the TextEdit gets the focus back.

        :param colour_name: String of the selected text
        :return: N/A
        """
        self.win.textedit_Notes.setTextColor(ColourCodes[colour_name.upper()].value)
        self.win.textedit_Notes.setFocus()

    # don't use native signals/slot, so focus can be set back to edit box
    @Slot()
    def set_notes_font(self):
        """
        Actions required for changing the TextEdit font. Ensure that the TextEdit gets the focus back.

        :return: N/A
        """
        self.win.textedit_Notes.setCurrentFont(self.win.combo_Notes_Font.currentText())
        self.win.textedit_Notes.setFocus()


# def test() -> None:
#     notes_ui = NotesUI()
#     print(notes_ui)
#
#
# if __name__ == "__main__":
#     test()
