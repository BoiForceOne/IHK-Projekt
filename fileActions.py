import os
import sys
from PySide6.QtWidgets import * #type: ignore

from consts import ID_COLUMN, COUNT_COLUMN
import db
from state import Settings, State, mainWindow

def select_folder_dialog():
    """
    opens folderDialog

    :return: returns string containing the selected path and '' if selection was interupted
    """ 
    file_path = QFileDialog.getExistingDirectory(None, "Select a folder")

    return file_path


def selectFileDialog(title: str):
    """
    opens fileDialog

    Returns
    -------
    returns string containing the selected path and None if selection was interupted
    """ 
    file_path, _ = QFileDialog.getOpenFileName(None, title, "", "Excel Files (*.xlsx)")

    return file_path


def saveScannedToExcel(state: State):
    """
    Saves the filtered dataframe to an excel file.
    :return: none
    """
    saveFolderPath = select_folder_dialog()
    if saveFolderPath == "":  # if no folder was selected, return
        return
    filteredDf = db.newDfWithScannedIDs(state.data)
    filteredDf[COUNT_COLUMN] = filteredDf[ID_COLUMN].map(state.data.anzahlScannedItems)  # type: ignore
    outputFilePath = os.path.join(saveFolderPath, "Einkaufsliste.xlsx")
    filteredDf.to_excel(outputFilePath, index=False)  # type: ignore
    QMessageBox.information(
        mainWindow(), "Erfolg", f"Einkaufsliste gespeichert unter {outputFilePath}"
    )
    return


def showSelectFileDialog(settings: Settings, title: str, message: str):

    diag = QDialog(mainWindow())
    diag.setWindowTitle(title)
    diag.setMinimumWidth(500)

    layout = QVBoxLayout()

    label = QLabel(message)
    layout.addWidget(label)

    info = QLabel("")
    layout.addWidget(info)

    # Path inputs
    inputLayout = QHBoxLayout()

    input = QLineEdit()
    input.setPlaceholderText("Pfad zur Datei")
    input.setText(settings.filePath)
    input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    inputLayout.addWidget(input)

    fileBrowseButton = QPushButton("Auswählen")
    inputLayout.addWidget(fileBrowseButton)

    layout.addLayout(inputLayout)

    # Buttons
    buttonLayout = QHBoxLayout()
    buttonLayout.addStretch(1)

    cancelButton = QPushButton("Abbrechen")
    buttonLayout.addWidget(cancelButton)

    confirmButton = QPushButton("Weiter")
    buttonLayout.addWidget(confirmButton)

    layout.addLayout(buttonLayout)

    def selectFile():
        filePath = selectFileDialog(title)
        if filePath == "":
            return
        settings.filePath = filePath
        input.setText(filePath)
        confirm()

    def cancel():
        diag.reject()
        sys.exit()

    def confirm():
        try:
            db.newDataFromExel(settings.filePath)
        except ValueError as e:
            info.setText(e.args[0])
            return
        diag.accept()

    def textChanged():
        settings.filePath = input.text()

    fileBrowseButton.clicked.connect(selectFile)
    cancelButton.clicked.connect(cancel)
    confirmButton.clicked.connect(confirm)
    input.textChanged.connect(textChanged)

    diag.setLayout(layout)

    # Dialogfeld anzeigen
    confirm()
    diag.adjustSize()
    diag.exec()
    return db.newDataFromExel(settings.filePath)


def loadValideExcel(settings: Settings):
    """
    Returns the data from the excel file specified in the settings.
    If the file does not exist or is invalide, the user is prompted to select a new file.
    The function does not raise any errors and only returns when the file is successfully loaded.

    Parameters
    ----------
    settings : The settings struct containing the file path

    Returns
    -------
    The data struct
    """
    try:
        return db.newDataFromExel(settings.filePath)
    except ValueError:
        return showSelectFileDialog(settings, "Exel-Datei auswählen", "Bitte wählen Sie eine gültige Excel-Datei aus.")
