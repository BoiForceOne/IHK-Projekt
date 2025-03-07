from dataclasses import dataclass
from typing import Self
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QMainWindow,
    QTableWidget,
)

import pandas as pd

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
    children: list[Self]
    parent: Self | None
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
    storageLocationsDict : Contains the layout of all the Locations as the dict read from the config file
        This is used in the settings window to display edit the locations
        Updates storageLocations when saving the settings or reading the config file
        For now this is the source of truth, but it should be replaced by storageLocations
    storageLocations : Contains the layout of all the Locations
        Example:
        ```
        {
            "Area.01": {
                "Regal 1": {
                    "Schublade 1": {
                        "id": "d32c8f6c-9c58-40d6-97b7-94659dc9f921"
                    },
                    "id": "3bcf7e40-c5e5-4a15-8ef2-77a750bb084e"
                },
                "id": "f7428ce1-7916-4771-bad9-9d9efa5e27da"
            },
            "Keller": {
                "Lasercutterregal": {
                    "id": "22775ee1-dc5f-4bef-811c-ae87ceb9ea3c"
                },
                "Regal 1": {
                    "id": "6351eeee-81eb-44d4-9132-b739adbba2bb"
                },
                "id": "543e0cbe-d19c-4760-bbe6-2d1438f023ae"
            }
        }
        ```

    """
    filePath: str
    language: str
    unitSystem: str
    persistScannedIDs: bool
    locations: list[Location]


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
    _df : The dataframe that holds the data from the excel file.
        Should not be used directly, instead use the ``db`` Module to get data.
    """

    tableHeaders: list[str]
    dataHeaders: list[str]
    scannedIDs: list[int]
    anzahlScannedItems: dict[int, int]
    df: pd.DataFrame

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
    Reassing the struct will not change it and should not be done/needed.

    Parameters
    ----------
    filePath : The path to the exel file that is currently used
    data : The data that is currently used
    gui : The gui that is currently used
        None before the gui is created
    multiplier : The multiplier that is currently used when scanning codes
    delMode : If the delete mode is active
    """

    data: Data
    gui: GUI | None
    settings: Settings
    multiplier: int
    delMode: bool

    def setMultiplier(self, value: int):
        self.multiplier = value
