import random
from PySide6.QtWidgets import (
    QLineEdit,
    QComboBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QSpinBox,
)
import db
from locationWidget import createLocationPicker
from qrGenerator import *
from consts import *
from location import getLocationString
from state import Location, State


def focus(fields: dict[str, QLineEdit | QComboBox | QSpinBox], column: str):
    def inner():
        fields[column].setFocus()

    return inner


def entryWindow(state: State, row: db.Row):
    """
    Shows the entry window for the given row.
    Consider using ``addEntryWindow()`` or ``editEntryWindow()`` for ease of use.
    """
    assert state.gui is not None

    def saveEntries():
        """
        Saves entries to the database and closes the entry window.

        The ``fields`` param hold a dict of Column names to ui
        """
        for column in fields:
            if column == LOCATION_COLUMN:
                continue
            value = getFieldValue(fields[column])
            row.setValue(column, value)
        row.write(state.data, state.settings.filePath)
        window.close()

    def deleteEntry(row: db.Row):
        """
        Deletes the given entry from the database.
        """
        confirmation = QMessageBox.question(
            window,
            "Löschen Bestätigen",
            "Sind Sie sich sicher, dass sie diesen Eintrag löschen?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No,
        )
        if confirmation == QMessageBox.StandardButton.Yes:
            row.delete(state.data, state.settings.filePath)
            window.close()
        else:
            pass

    def showLocationPicker(state: State, row: db.Row):
        locationWidget: QWidget

        def onLocationPicked(location: Location | None):
            if location is not None:
                row.setValue(LOCATION_COLUMN, location.id)
            field = fields[LOCATION_COLUMN]
            assert isinstance(field, QLineEdit)
            field.setText(getLocationString(state.data.locations, row.getValue(LOCATION_COLUMN)))
            locationWidget.close()

        locationWidget = createLocationPicker(state, onLocationPicked)
        locationWidget.setWindowTitle("Lagerort auswählen")
        locationWidget.show()

    window = QWidget()
    window.setWindowTitle("Eintrag")

    layout = QVBoxLayout()

    fields: dict[str, QLineEdit | QComboBox | QSpinBox] = {}

    prevInput = None

    for column in state.data.dataHeaders:
        if column == LOCATION_COLUMN:
            layout.addWidget(QLabel("Lagerort"))
            lRow = QHBoxLayout()

            lLineEdit = QLineEdit()
            lLineEdit.setDisabled(True)
            lRow.addWidget(lLineEdit)

            btn = QPushButton("🖉")
            btn.clicked.connect(lambda: showLocationPicker(state, row))
            lRow.addWidget(btn)

            layout.addLayout(lRow)
            fields[LOCATION_COLUMN] = lLineEdit
        elif column == ID_COLUMN:
            continue
        elif column == STORED_AMOUNT_COLUMN:
            layout.addWidget(QLabel(column))
            hbox = QHBoxLayout()
            spinBox = QSpinBox()
            spinBox.setMaximum(999999)
            spinBox.setValue(int(row.getValue(column)) if row.getValue(column).isdigit() else 1)
            hbox.addWidget(spinBox)
            layout.addLayout(hbox)
            fields[column] = spinBox
        else:
            layout.addWidget(QLabel(column))
            lineedit = QLineEdit()
            if column in Examples:
                lineedit.setPlaceholderText(f"{Examples[column]}")
            fields[column] = lineedit
            layout.addWidget(fields[column])
            if type(prevInput) is QLineEdit:
                prevInput.returnPressed.connect(focus(fields, column))
            prevInput = fields[column]

    editButton = QPushButton("Speichern")
    editButton.clicked.connect(lambda: saveEntries())
    layout.addWidget(editButton)

    if type(prevInput) is QLineEdit:
        prevInput.returnPressed.connect(saveEntries)

    saveQrButton = QPushButton("QR-Code speichern")
    saveQrButton.clicked.connect(lambda: saveQRCode(fields))
    layout.addWidget(saveQrButton)

    deleteFromDBButton = QPushButton("Eintrag löschen")
    deleteFromDBButton.clicked.connect(lambda: deleteEntry(row))
    layout.addWidget(deleteFromDBButton)

    window.setLayout(layout)

    # Loading Entry into fields
    for column in fields:
            
        value = row.getValue(column)
        field = fields[column]
            
        if type(field) == QLineEdit:
            if column == LOCATION_COLUMN:
                field.setText(getLocationString(state.data.locations, value))
                continue
            field.setText(value)
            field.setEnabled(True)
        elif type(field) == QComboBox:
            field.addItem(value)
            field.setCurrentText(value)
            field.setEnabled(True)
        elif type(field) == QSpinBox:
            field.setValue(int(value) if value.isdigit() else 1)
            field.setEnabled(True)

    fields[TYPE_COLUMN].setFocus()

    window.show()
    while window.isVisible():
        state.gui.app.processEvents()


def editEntryWindow(state: State, id: int):
    """
    Shows the entry window for the entry with the given id.
    """
    entryWindow(state, db.newRow(state.data, id))


def addEntryWindow(state: State):
    """
    Shows the entry window for a new entry.
    The id is automagically selected and the code is prefilled.
    """
    ul: list[str] = list(state.data.df[ID_COLUMN])  # type: ignore
    sorted_list: list[int] = [int(i) for i in ul]
    sorted_list.sort()
    next_id = sorted_list[-1] + 1 if not state.data.df.empty else 1

    code = ""
    while True:
        code = str(random.randint(0, 9999999999)).zfill(10)
        shoudBeEmpty = db.newRowFromCode(state.data, code)
        if shoudBeEmpty.empty():
            break

    row: db.Row = db.newRow(state.data, sorted_list[0])
    for column in state.data.dataHeaders:
        if column == CODE_COLUMN:
            row.setValue(column, code)
        elif column == ID_COLUMN:
            row.setValue(column, next_id)
        else:
            row.setValue(column, "")
    row.scanCount = 1
    entryWindow(state, row)


def getFieldValue(field: QLineEdit | QComboBox | QSpinBox) -> str:
    if type(field) == QComboBox:
        value = field.currentText().strip()
        value = "" if value.endswith("auswählen") else value
        return value
    elif type(field) == QLineEdit:
        return field.text().strip()
    elif type(field) == QSpinBox:
        return str(field.value())
    else:
        raise TypeError("Field is not a QLineEdit or QComboBox")


def saveQRCode(fields: dict[str, QLineEdit | QComboBox | QSpinBox]):
    code_field = fields[CODE_COLUMN]
    assert type(code_field) == QLineEdit
    code = code_field.text()
    if not code:
        QMessageBox.warning(window(), "Warnung", "Kein Code zum Speichern vorhanden!")  # type: ignore
        return

    # Todo: Use the fileActions module
    file_name, _ = QFileDialog.getSaveFileName(
        None, "QR-Code speichern", f"{code}.png", "PNG-Dateien (*.png)"
    )

    if file_name:
        data_matrix = generate_data_matrix(code)
        data_matrix.save(file_name, scale=10)
        QMessageBox.information(window(), "Erfolg", f"QR-Code gespeichert als {file_name}")  # type: ignore


