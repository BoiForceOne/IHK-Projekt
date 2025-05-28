from PySide6.QtGui import QIcon
import sys
from entries import *
from consts import *
import db
from settings import *
from manualDisplay import *
from state import *
import fileActions as files
from scanView import createScanView


def main():
    
    # Application Window
    app = QApplication(sys.argv)
    w = QMainWindow()
    w.setWindowTitle("Logistic.01")
    w.setWindowIcon(QIcon("assets/logo.png"))
    setWindow(w)

    settings: Settings = readSettings()
    

    # Entry Point
    data: Data = files.loadValideExcel(settings)
    if settings.persistScannedIDs:
        db.loadIDsAndCount(data, SCANNED_IDS_FILE_PATH)
        db.validateIDs(data)

    state = State(
        data=data, 
        gui=None, 
        settings=settings, 
        multiplier=1
)

    rootWidget = createScanView(state, app, w)
    w.setCentralWidget(rootWidget)

    w.showMaximized()
    app.exec()

    writeSettings(state.settings)
    if settings.persistScannedIDs:
        db.saveScannedIDs(state.data, SCANNED_IDS_FILE_PATH)


if __name__ == "__main__":
    main()
