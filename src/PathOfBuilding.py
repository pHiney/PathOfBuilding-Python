# nuitka-project: --standalone
# nuitka-project: --onefile
# nuitka-project: --onefile-windows-splash-screen-image=Assets/PathOfBuilding.png
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-data-dir=src/data=data
# nuitka-project: --windows-icon-from-ico=Assets/Icons/PathOfBuilding.ico
# nuitka-project: --onefile-tempdir-spec='{TEMP}/PoB_{PID}'
# nuitka-project: --onefile-no-compression
# nuitka-project: --include-plugin-directory=src/dialogs
# nuitka-project: --clean-cache=all
# nuitka-project: --python-flag=static_hashes
# nuitka-project: --disable-console
# nuitka -project: --quiet
# nuitka- project: --debug
# nuitka- project: --trace
# nuitka- project: --experimental=disable-freelist-all

"""
Path of Building main executable.

Icons by  Yusuke Kamiyamane (https://p.yusukekamiyamane.com/)
Splashscreen by https://creator.nightcafe.studio
"""
import glob
import os
import sys
import tempfile

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt

from windows.main_window import MainWindow

#############################################################################################################
# Start here

# This is  NUITKA debugging info so folk can understand the difference between the extracted directory and
# the directory the Executable was run from:
# import os
#
# print("os.getcwd", os.getcwd())
# if "NUITKA_ONEFILE_PARENT" in os.environ:
#     print("TEMP: ", os.environ["TEMP"])
#     print("NUITKA_ONEFILE_PARENT: ", os.environ["NUITKA_ONEFILE_PARENT"])
#     print(os.listdir(os.environ["NUITKA_ONEFILE_PARENT"]))

# This is pyInstaller debugging info so folk can understand the difference between the extracted directory and
# the directory the Executable was run from:

# print("os.getcwd", os.getcwd())
# if getattr(sys, "_MEIPASS", 0) != 0:
#     print("TEMP: ", os.environ["TEMP"])
#     print("_MEIPASS: ", sys._MEIPASS)
#     os.chdir(sys._MEIPASS)
#     print(os.listdir(sys._MEIPASS))

# from time import sleep
# sleep(60)


def clear_splash_screen():
    """
    Remove splash screen if we are an executable.
    Use this code to signal the splash screen removal.
    """
    splash_filenames = glob.glob(f"{tempfile.gettempdir()}/onefile_*_splash_feedback.tmp")
    for filename in splash_filenames:  # splash_filenames is a [list]
        os.unlink(filename)


# Logging to a file, not spam to screen or get lost if no console
# ToDo: Remove comment when we stop building.
# sys.stdout = open("PathOfBuilding.log", 'a')


QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
main_app = QApplication(sys.argv)

# font for stats box. To line things up, we need a Mono font. (could use <pre> html tag now that I know it exists. PSH 20230802)
QFontDatabase.addApplicationFont(":/Font/Font/NotoSansMono-Regular.ttf")
# system wide font
QApplication.setFont(QFont(":Font/Font/NotoSans-Regular.ttf", 9))

window = MainWindow(main_app)
x, y = window.settings.pos
# why do we need to add 31 to y value to keep the window in position (and not drift up the screen).
window.setGeometry(x, y + 31, window.settings.width, window.settings.height)
window.setup_ui()
window.show()
if "NUITKA_ONEFILE_PARENT" in os.environ:
    clear_splash_screen()
main_app.exec()
