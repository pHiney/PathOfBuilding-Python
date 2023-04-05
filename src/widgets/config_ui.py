"""
This Class manages all the elements and owns some elements of the "CONFIG" tab
"""

from qdarktheme.qtpy.QtCore import (
    QCoreApplication,
    QDir,
    QRect,
    QRectF,
    QSize,
    Qt,
    Slot,
)
from qdarktheme.qtpy.QtGui import (
    QAction,
    QActionGroup,
    QFont,
    QIcon,
    QPixmap,
    QBrush,
    QColor,
    QPainter,
)
from qdarktheme.qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFontComboBox,
    QFontDialog,
    QFormLayout,
    QFrame,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QStyle,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QToolBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from views.PoB_Main_Window import Ui_MainWindow
from pob_config import Config
from ui_utils import set_combo_index_by_data

# from constants import _VERSION
# from ui_utils import FlowLayout


class ConfigUI:
    def __init__(self, _config: Config, _build, _win: Ui_MainWindow) -> None:
        self.pob_config = _config
        self.win = _win
        self.build = _build

    def load(self, _config):
        """
        Load internal structures from the build object
        :param _config: Reference to the xml <Config> tag set
        """
        set_combo_index_by_data(self.win.combo_ResPenalty, self.build.resistancePenalty)
        set_combo_index_by_data(self.win.combo_Bandits, self.build.bandit)
        set_combo_index_by_data(self.win.combo_MajorGods, self.build.pantheonMajorGod)
        set_combo_index_by_data(self.win.combo_MinorGods, self.build.pantheonMinorGod)

    def save(self):
        """
        Save internal structures back to the build object
        """
        self.build.resistancePenalty = self.win.combo_ResPenalty.currentData()
        self.build.bandit = self.win.combo_Bandits.currentData()
        self.build.pantheonMajorGod = self.win.combo_MajorGods.currentData()
        self.build.pantheonMinorGod = self.win.combo_MinorGods.currentData()


def test() -> None:
    config_ui = ConfigUI()
    print(config_ui)


if __name__ == "__main__":
    test()