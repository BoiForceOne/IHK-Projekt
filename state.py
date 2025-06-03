from dataclasses import dataclass
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QMainWindow,
    QTableWidget,
)

import pandas as pd
from typing import Union

__window: QMainWindow


def setWindow(window: QMainWindow):
    global __window
    __window = window


def mainWindow() -> QMainWindow:
    return __window


class Lock:
    __locked: bool

    def __init__(self) -> None:
        self.__locked = False

    def __enter__(self):
        if self.__locked:
            raise RuntimeError("Lock is already locked, check before entering")
        self.__locked = True
        return

    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore
        self.__locked = False
        return False

    @property
    def locked(self):
        return self.__locked


@dataclass
class InputBar:
    """
    Struct that holds references to important ui elements for the input bar.
    Is returned by the ``main.createInputBar()`` method.

    Part of the ``GUI`` struct.

    Parameters
    ----------
    text : reference to the QLineEdit that holds the code scanned code
    multiplierBox : reference to the QSpinBox that holds the multiplier
    button : reference to the QPushButton that triggers the code reading
    """

    text: QLineEdit
    multiplierBox: QSpinBox
    button: QPushButton


@dataclass
class MenuBar:
    """
    Struct that holds references to important ui elements for the menu bar.
    Is returned by the ``main.createMenuBar()`` method.

    Part of the ``GUI`` struct.

    Parameters
    ----------
    saveToExcelButton : reference to the QPushButton that saves the data to an excel file
    addEntryButton : reference to the QPushButton that adds a new entry to the data
    """

    saveToExcelButton: QPushButton
    addEntryButton: QPushButton


@dataclass
class GUI:
    """
    Struct that holds references to important ui elements.

    The ``app`` and ``window`` need to be created seperately.
    Then the ``main.createRootWidget()`` method will create the main application view and fill the struct.
    The ``app`` and ``window`` need to be present in the GUI struct or passed on to the ``main.createRootWidget()`` method.

    Part of the ``State`` struct.

    Parameters
    ----------
    app : The UI Application Context.
    table : The table widget.
    inputBar : Reference to the inputBar struct.
    menuBar : Reference to the menuBar struct.
    """

    app: QApplication
    window: QMainWindow
    table: QTableWidget
    inputBar: InputBar
    menuBar: MenuBar


@dataclass
class Location:
    name: str
    id: str
    parent: Union[str, None]
    expanded: bool = False


@dataclass
class Settings:
    """
    All the Settings in one handy pack.

    Load from settings file with the ``settings.readConfig()`` method.

    Part of the ``State`` struct.

    Parameters
    ----------
    filePath : The file path to the excel file. Modifing this will NOT reload the data. Use ``db.reloadFromFile()`` to reload the data.
    language : The display language (Example)
    unitSystem : Which Unit System ("Metrisch" doer "Imperial") to use (Test)
    persistScannedIDs : Whether to persist the scanned IDs over sessions

    """

    filePath: str
    language: str
    unitSystem: str
    persistScannedIDs: bool


@dataclass
class DBInfo:
    """
    Infos about the database

    Parameters
    ----------
    version : The olderst version of the Programm that this DB is compatible with / The version of the Programm that last broke compatability.
    """

    version: str


@dataclass
class Data:
    """
    Struct that holds the data of the application.

    This is created from the Database (Excel-File) with the ``db.newDataFromExel()`` method

    Ist is part of the State struct.

    Parameters
    ----------
    tableHeaders : The headers of the table (names of the columns).
    dataHeaders : The headers of the database table.
    scannedIDs : The IDs of the scanned entries.
    anzahlScannedItems : The amount scanned for each entries.
        Use ``db.syncIdsWithCount()`` to make sure that this matches the scannedIDs list.
    df : The dataframe that holds the data from the excel file.
        Should not be used directly, instead use the ``db`` Module to get data.
    locations : A list of all Locations
    """

    tableHeaders: list[str]
    dataHeaders: list[str]
    scannedIDs: list[int]
    anzahlScannedItems: dict[int, int]
    df: pd.DataFrame
    locations: list[Location]
    info: DBInfo

    def addId(self, id: int):
        if id not in self.scannedIDs:
            self.scannedIDs.append(id)
            self.anzahlScannedItems[id] = 1
        else:
            self.anzahlScannedItems[id] += 1

    def rowCount(self) -> int:
        return len(self.scannedIDs)

    def columnCount(self) -> int:
        return len(self.tableHeaders)

    def scanCount(self, id: int) -> int:
        if id not in self.anzahlScannedItems:
            return 0
        return self.anzahlScannedItems[int(id)]

    def setScanCount(self, id: int, scanCount: int):
        self.anzahlScannedItems[id] = scanCount


@dataclass
class State:
    """
    Struct that holds the state of the application.

    This Struct is created in the main function and passed by parameter to all other functions.

    Modifing the struct and it contents will change it everywhere, no returning is needed.
    (exept when direct references to parts of the State are held. Which happen too often at the moment)
    Reassing the struct will not change it and should not be done/needed.

    Parameters
    ----------
    data : The data that is currently used
    gui : The gui that is currently used; None before the gui is created
    settings : The settings that are currently used
    multiplier : The multiplier that is currently used when scanning codes
    currentmode : If the add, remove mode is active
    """

    data: Data
    gui: GUI | None
    settings: Settings
    multiplier: int
    current_mode: str | None = "remove"