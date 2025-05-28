import sys
from consts import *
import db
from entries import addEntryWindow, editEntryWindow
from location import getLocationString
from manualDisplay import createManualView
import search
from typing import Callable

import webbrowser
from PySide6.QtCore import QModelIndex, QPersistentModelIndex
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QSpinBox,
)
from settings import createSettings
from state import *
import os
import fileActions as files
from db import headerIndex


def addIdListener(state: State, id: int):
    assert state.gui is not None
    state.data.addId(id)
    updateMenuBar(state.data, state.gui.menuBar)
    updateTable(state, state.gui.table)


def readCodeListener(state: State):
    assert state.gui is not None
    addIdForCode(state, state.gui.inputBar.text.text())
    updateInputBar(state, state.gui.inputBar)
    updateMenuBar(state.data, state.gui.menuBar)
    updateTable(state, state.gui.table)


def clearTable(state: State):
    assert state.gui is not None
    db.clearScanned(state.data)
    updateTable(state, state.gui.table)


def showSettings(state: State):
    assert state.gui is not None
    state.gui.window.setCentralWidget(
        createSettings(state, lambda: showScannView(state))
    )

def reloadData(state: State):
    assert state.gui is not None
    db.reloadFromFile(state.data, state.settings.filePath)
    updateTable(state, state.gui.table)


def showScannView(state: State):
    assert state.gui is not None
    state.gui.window.setCentralWidget(createScanView(state))


def showHelp(state: State):
    assert state.gui is not None
    state.gui.window.setCentralWidget(
        createManualView(state, lambda: showScannView(state))
    )


def updateTable(state: State, table: QTableWidget):
    """
    Redraws the Table with the entries with the IDs in 'scannedIDs' and the columns with the headers in 'headers'
    Handles special columns like the URLs and the Edit Buttons

    Parameters
    ----------
    data : Data to be displayed in the table
    table : The Table the entries are going to be displayed in (mutated)
    """
    data = state.data
    db.validateIDs(data)
    # Row and Columns of the Table
    table.clear()
    table.setRowCount(data.rowCount())
    table.setColumnCount(data.columnCount())
    table.setHorizontalHeaderLabels(data.tableHeaders)

    db.syncIdsWithCount(data)

    for row in range(data.rowCount()):
        # Get the row of the dataframe that corresponds to the current row in the table
        dataRow: db.Row = db.newRowFromIndex(data, row)

        for column, header in enumerate(data.tableHeaders):
            if header == EDIT_COLUMN:
                # Logic to display the Edit Button
                item = QTableWidgetItem()
                table.setItem(row, column, item)
                table.openPersistentEditor(item)
            elif header == DELETE_COLUMN:
                item = QTableWidgetItem()
                table.setItem(row, column, item)
                table.openPersistentEditor(item)
            elif header == COUNT_COLUMN:
                item = QTableWidgetItem()
                item.setText(str(dataRow.scanCount))
                table.setItem(row, column, item)
                table.openPersistentEditor(item)
            elif header == LOCATION_COLUMN:
                item = QTableWidgetItem()
                item.setText(
                    getLocationString(
                        state.data.locations,
                        dataRow.getValue(LOCATION_COLUMN),
                    )
                )
                table.setItem(row, column, item)
            else:
                value = dataRow.getValue(header)
                # Logic to display a cickable url
                if header == URL_DATASHEET_COLUMN and value != "":
                    item = QTableWidgetItem("🗏 Link öffnen")
                    item.setToolTip(value)
                elif header == URL_ORDER_COLUMN and value != "":
                    item = QTableWidgetItem("🛒 Link öffnen")
                    item.setToolTip(value)
                else:
                    # This line and the following one are needed to display the value directly in the table
                    # All the other logic is needed for spectial columns like URLs and Buttons
                    item = QTableWidgetItem(value)
                table.setItem(row, column, item)
    table.resizeColumnToContents(data.tableHeaders.index(LOCATION_COLUMN))


def clickCell(data: Data, item: QTableWidgetItem):
    """
    An event Listener for the Table.
    Pass this to ``QTableWidget.itemClicked.connect()``.

    Parameters
    ----------
    item : The QTableWidgetItem that was clicked
    """
    header = data.tableHeaders[item.column()]
    value = db.newRowFromIndex(data, item.row()).getValue(header)
    if (
        header == URL_DATASHEET_COLUMN or header == URL_ORDER_COLUMN
    ) and value != "nan":
        webbrowser.open(value)


def addEntryClicked(state: State):
    addEntryWindow(state)
    assert state.gui is not None
    updateMenuBar(state.data, state.gui.menuBar)
    updateTable(state, state.gui.table)


class EditButtonDelegate(QStyledItemDelegate):
    """
    The edit button in the table

    This class is one of the multiple steps to add arbitrary widgets to the Table
    The most important part is the 'createEditor()' method which sets the editor of a cell to be the widget
    For each widget with a different functionality, a new class is needed
    The other steps are:
    - set the column of the table to use the delegate ('QTableWidget.setItemDelegateForColumn()')
    - set each cell to be the editor by default ('QTableWidget.openPersistentEditor()')
    :param parent: The parent of the delegate, which is the TableWidget
    """

    def __init__(self, state: State, table: QTableWidget):
        super(EditButtonDelegate, self).__init__(table)
        self.state = state
        self.table = table

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        def edit():
            assert self.state.gui is not None
            editEntryWindow(self.state, self.state.data.scannedIDs[index.row()])
            updateTable(self.state, self.table)

        button = QPushButton(parent)
        button.setText("✏️")
        button.clicked.connect(edit)
        return button


class DeleteButtonDelegate(QStyledItemDelegate):
    """
    The delete button in the table

    This class is one of the multiple steps to add arbitrary widgets to the Table
    The most important part is the 'createEditor()' method which sets the editor of a cell to be the widget
    For each widget with a different functionality, a new class is needed
    The other steps are:
    - set the column of the table to use the delegate ('QTableWidget.setItemDelegateForColumn()')
    - set each cell to be the editor by default ('QTableWidget.openPersistentEditor()')
    :param parent: The parent of the delegate, which is the TableWidget
    """

    def __init__(
        self, state: State, table: QTableWidget, updateMenuBar: Callable[[], None]
    ):
        super(DeleteButtonDelegate, self).__init__(table)
        self.state = state
        self.table = table
        self.updateMenuBar = updateMenuBar

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        button = QPushButton(parent)
        button.setText("🗑")
        button.clicked.connect(lambda: self.deleteEntry(index.row()))
        return button

    def deleteEntry(self, row: int):
        id_to_remove = self.state.data.scannedIDs[row]
        self.state.data.scannedIDs.remove(id_to_remove)
        self.state.data.anzahlScannedItems.pop(id_to_remove)
        self.updateMenuBar()
        updateTable(self.state, self.table)


class CounterDelegate(QStyledItemDelegate):
    """
    The conter spinBox in the table

    This class is one of the multiple steps to add arbitrary widgets to the Table
    The most important part is the 'createEditor()' method which sets the editor of a cell to be the widget
    For each widget with a different functionality, a new class is needed
    The other steps are:
    - set the column of the table to use the delegate ('QTableWidget.setItemDelegateForColumn()')
    - set each cell to be the editor by default ('QTableWidget.openPersistentEditor()')
    :param parent: The parent of the delegate, which is the TableWidget
    """

    def __init__(self, state: State, table: QTableWidget):
        super(CounterDelegate, self).__init__(table)
        self.state = state
        self.table = table

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        AnzSpinBox = QSpinBox(parent)
        AnzSpinBox.setRange(1, 999999)
        AnzSpinBox.setValue(
            self.state.data.anzahlScannedItems.get(
                self.state.data.scannedIDs[index.row()], 1
            )
        )  # Default to 1 if not found
        AnzSpinBox.valueChanged.connect(
            lambda: self.updateCount(AnzSpinBox.value(), index.row())
        )  # Update the count when the value changes
        return AnzSpinBox

    def updateCount(self, value: int, row: int):
        id_to_update = self.state.data.scannedIDs[row]
        self.state.data.anzahlScannedItems[id_to_update] = value
        updateTable(self.state, self.table)


def createInputBar(state: State):
    """
    Creates the input widget and the struct that inputBar.

    Does not add the input widget to the rootLayout, nor the inputBar to the GUI struct.
    Do this by calling ``rootLayout.addWidget(inputWidget)`` and ``gui.inputBar = inputBar``.

    Parameters
    ----------
    state : The current state of the application

    Returns
    -------
    widget : The UI element
        Needs to be added to the rootLayout
    inputBar : The inputBar struct
        Needs to be added to the GUI struct
    """

    # Hold all the Input Elements in a Horizontal Orientation
    inputLayout = QHBoxLayout()

    inputWidget = QWidget()
    inputWidget.setLayout(inputLayout)

    # TextField for Inputing the Code
    text = QLineEdit()
    text.setPlaceholderText("Scan DMC- oder Bar Code")
    text.returnPressed.connect(lambda: readCodeListener(state))
    inputLayout.addWidget(text)
    # Focus on the TextField after the Window was shown
    text.setFocus()

    # multiplier label
    label = QLabel("x")
    inputLayout.addWidget(label)

    # SpinBox for Multiplier-selection
    multiplierBox = QSpinBox()
    multiplierBox.setRange(1, 1000)
    multiplierBox.setValue(1)
    multiplierBox.valueChanged.connect(
        lambda: state.setMultiplier(multiplierBox.value())
    )
    inputLayout.addWidget(multiplierBox)

    # Butten for Triggering the Code read
    button = QPushButton("Add")
    button.setStyleSheet(f"background: rgb(255, 165, 0); color: rgb(0, 0, 0);")
    button.pressed.connect(lambda: readCodeListener(state))
    inputLayout.addWidget(button)
    inputBar = InputBar(text, multiplierBox, button)
    
    return inputWidget, inputBar


def createTable(state: State, onDelete: Callable[[], None]):
    table = QTableWidget()
    table.itemClicked.connect(lambda item: clickCell(state.data, item))  # type: ignore
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    table.setItemDelegateForColumn(
        state.data.tableHeaders.index("Edit"), EditButtonDelegate(state, table)
    )
    table.setItemDelegateForColumn(
        state.data.tableHeaders.index("Delete"),
        DeleteButtonDelegate(state, table, onDelete),
    )
    table.setItemDelegateForColumn(
        state.data.tableHeaders.index("Anzahl"), CounterDelegate(state, table)
    )
    return table


def createMenuBar(state: State):
    menuLayout = QHBoxLayout()

    menuWidget = QWidget()
    menuWidget.setLayout(menuLayout)

    # Buttons for adding new Entries to the Table
    addEntryButton = QPushButton("➕")
    addEntryButton.setFixedSize(30, 30)
    addEntryButton.setToolTip("Neuen Eintrag hinzufügen")
    addEntryButton.clicked.connect(lambda: addEntryClicked(state))

    menuLayout.addWidget(addEntryButton)

    # Button for dumping the scanned Entries to a new Excel File
    saveToExcelButton = QPushButton("💾")
    saveToExcelButton.setFixedSize(30, 30)
    saveToExcelButton.setToolTip("Einträge in eine neue Excel Datei speichern")
    saveToExcelButton.clicked.connect(lambda: files.saveScannedToExcel(state))

    menuLayout.addWidget(saveToExcelButton)

    # Button for clearing all scanned Entries from the UI
    searchButton = QPushButton("🔍")
    searchButton.setFixedSize(30, 30)
    searchButton.setToolTip("Einträge durchsuchen")
    searchButton.clicked.connect(
        lambda: search.showSearch(state.data, lambda id: addIdListener(state, id))
    )

    menuLayout.addWidget(searchButton)

    # Button for clearing all scanned Entries from the UI
    clearAllButton = QPushButton("❌")
    clearAllButton.setFixedSize(30, 30)
    clearAllButton.setToolTip("Einträge löschen")
    clearAllButton.clicked.connect(lambda: clearTable(state))

    menuLayout.addWidget(clearAllButton)

    # Button for help
    helpButton = QPushButton("❔")
    helpButton.setFixedSize(30, 30)
    helpButton.setToolTip("Hilfe")
    helpButton.clicked.connect(lambda: showHelp(state))

    menuLayout.addWidget(helpButton)

    # Button for opening the settings menu
    settingsButton = QPushButton("⚙️")
    settingsButton.setFixedSize(30, 30)
    settingsButton.setToolTip("Einstellungen öffnen")
    settingsButton.clicked.connect(lambda: showSettings(state))

    menuLayout.addWidget(settingsButton)

    # Button for opening the settings menu
    reloadButton = QPushButton("↻")
    reloadButton.setFixedSize(30, 30)
    reloadButton.setToolTip("Lade die aktuelle Excel Datei neu.")
    reloadButton.clicked.connect(lambda: reloadData(state))

    menuLayout.addWidget(reloadButton)

    menuSpacer = QSpacerItem(
        10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
    )
    menuLayout.addItem(menuSpacer)

    # Assuming MenuBar is defined elsewhere
    menuBar = MenuBar(saveToExcelButton, addEntryButton)

    return menuWidget, menuBar


def updateInputBar(state: State, inputBar: InputBar):
    mode_text = {
        "add": "Auffüllen Modus",
        "remove": "Entnehmen Modus",
        None: "Nachkaufen Modus"
    }
    
    inputBar.text.setPlaceholderText(mode_text[state.current_mode])
    
    # Color coding
    bg_color = {
        "add": "#4CAF50",  # Green
        "remove": "#F44336",  # Red
        None: "#FFA500"  # Orange
    }[state.current_mode]
    
    inputBar.button.setStyleSheet(
        f"background: {bg_color};"
        "color: black;"
    )

    inputBar.multiplierBox.setStyleSheet(
        f"QSpinBox {{ background: white; color: black; }}" 
    )

    inputBar.multiplierBox.setValue(state.multiplier)


def updateMenuBar(data: Data, menuBar: MenuBar):
    """
    Updates the menu widget with the current state of the application.
    """
    menuBar.saveToExcelButton.setDisabled(data.rowCount() == 0)


def assertTrue(condition: bool, message: str):
    if not condition:
        print(f"[Assert Failed]: {message}")


def createScanView(
    state: State, app: QApplication | None = None, window: QMainWindow | None = None
):
    """
    Creates the main view of the application and fills the GUI struct inside the state.

    This method does NOT create the application and the window.
    The application and window need to be created seperately. Either store them in the GUI struct or pass them into this method, which will then store them in the GUI struct.

    Parameters
    ----------
    state : The Application state
    app : The Application UI context
    window : The MainWindow

    Returns
    -------
    rootWidget : The root widget of the application
        Still needs to be added to the window.

    Creating App and Window
    -----------------------
    >>> app = QApplication(sys.argv)
    >>>
    >>> w = QMainWindow()
    >>> w.setWindowTitle("Logistic.01")

    """

    if app is None:
        if state.gui is not None:
            app = state.gui.app
        else:
            print(
                "No app present in 'main.createRootWidget()'. Please pass it as a parameter or provide the GUI struct in the state."
            )
            sys.exit(1)

    if window is None:
        if state.gui is not None:
            window = state.gui.window
        else:
            print(
                "No window present in 'main.createRootWidget()'. Please pass it as a parameter or provide the GUI struct in the state."
            )
            sys.exit(1)

    assert app is not None and window is not None

    # Root Widget
    # Holds the Menu, Table and the Input Bar in a Vertical Orientation
    rootLayout = QVBoxLayout()

    rootWidget = QWidget()
    rootWidget.setLayout(rootLayout)

    # Menu, Table and Input Bar
    menuWidget, menuBar = createMenuBar(state)
    rootLayout.addWidget(menuWidget)

    table = createTable(state, lambda: updateMenuBar(state.data, menuBar))
    rootLayout.addWidget(table)

    inputWidget, inputBar = createInputBar(state)
    rootLayout.addWidget(inputWidget)

    inputBar.text.setFocus()

    state.gui = GUI(app, window, table, inputBar, menuBar)

    # Setting the initial state
    updateMenuBar(state.data, state.gui.menuBar)
    updateTable(state, state.gui.table)
    updateInputBar(state, state.gui.inputBar)
    return rootWidget

def addIdForCode(state: State, code: str):
    code = code.lower().strip()

    # Handle multiplier codes
    if code.startswith("mult"):
        try:
            multiplier = int(code[4:])  # Extract number after "mult"
            state.multiplier = multiplier

#            QMessageBox.information(mainWindow(), "Multiplikator Geändert", f"Multiplikator gesetzt auf {multiplier}")
            updateInputBar(state, state.gui.inputBar)
            return
        except ValueError:
            QMessageBox.warning(mainWindow(), "Warnung", "Ungültiger Multiplikator!")
            return
    
    # Handle mode codes
    if code == "addmode":
        state.current_mode = "add"
#        QMessageBox.information(mainWindow(), "Modus Geändert", "Auffüllen Modus aktiviert")
        return
    elif code == "removemode":
        state.current_mode = "remove"
#        QMessageBox.information(mainWindow(), "Modus Geändert", "Entnehmen Modus aktiviert")
        return
    elif code == "exitmode":
        state.current_mode = None
#        QMessageBox.information(mainWindow(), "Modus Geändert", "Nachkaufen Modus aktiviert")
        return

    # Handle item codes
    dataRow: db.Row = db.newRowFromCode(state.data, code)
    
    if dataRow.empty():
        QMessageBox.warning(mainWindow(), "Warnung", f"Eintrag '{code}' existiert nicht!")
        return

    if state.current_mode in ("add", "remove"):
        # Handle Stueckzahl updates
        stueck_index = headerIndex(state.data.dataHeaders, STORED_AMOUNT_COLUMN)
        current_stueck = int(dataRow.values[stueck_index]) if dataRow.values[stueck_index] else 0
        
        if state.current_mode == "add":
            new_value = current_stueck + state.multiplier
        else:
            new_value = max(0, current_stueck - state.multiplier)
            
        dataRow.values[stueck_index] = str(new_value)
        dataRow.write(state.data, state.settings.filePath)
    else:
        # Handle Anzahl updates
        dataRow.scanCount += state.multiplier
        dataRow.writeNoValues(state.data)

    updateTable(state, state.gui.table)
    updateInputBar(state, state.gui.inputBar)