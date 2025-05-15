from typing import Any, Callable
from PySide6.QtWidgets import (
    QMessageBox,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QLabel,
    QGroupBox,
    QRadioButton,
    QComboBox,
)

from consts import SETTINGS_FILE_PATH
import db
import os
from locationWidget import createLocationEditor
from state import *
import json
import copy

def settingsToDict(settings: Settings) -> dict[str, Any]:
    return {
        "filePath": settings.filePath,
        "language": settings.language,
        "persistScannedIDs": settings.persistScannedIDs,
        "unitSystem": settings.unitSystem,
    }

def writeSettings(settings: Settings):
    try:
        with open(SETTINGS_FILE_PATH, "w") as f:
            settingsDict = settingsToDict(settings)
            json.dump(settingsDict, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")


def readSettings():
    # Default values
    filePath = "Logistic_DB.xlsx"
    language = "German"
    unitSystem = "Imperial"
    persistScannedIDs = True

    # Settings File
    try:
        with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            filePath = data.get("filePath")
            language = data.get("language", "German")
            unitSystem = data.get("unitSystem", "Metrisch")
            persistScannedIDs = bool(data.get("persistScannedIDs", True))
    except Exception as e:
        print(f"Error reading settings file: {e}")

    config = Settings(
        language=language,
        unitSystem=unitSystem,
        persistScannedIDs=persistScannedIDs,
        filePath=filePath
    )
    return config


# --- File Selection Function ---


def selectExeclFile(filePathDisplay: QLineEdit):
    """Opens a file selection dialog and sets the file path to the selected file."""
    filePathDisplay.setStyleSheet("")
    fileDialog = QFileDialog()
    fileDialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    fileDialog.setNameFilter("Excel Files (*.xlsx *.xls)")
    fileDialog.setViewMode(QFileDialog.ViewMode.List)
    if fileDialog.exec():
        selectedFile = fileDialog.selectedFiles()[0]
        filePathDisplay.setText(f"{selectedFile}")


# --- UI Setup ---
def createSettings(state: State, closeSettings: Callable[[], None]):
    """Create and return the settings widget with UI and functionality."""
    assert state.gui is not None
    settingsWidget = QWidget()
    settingsLayout = QVBoxLayout()
    settingsWidget.setLayout(settingsLayout)
    settingsChanged = False
    # Create a temporary copy of the storage locations
    tempSettings = copy.deepcopy(state.settings)

    def setSettingsChanged():
        """Sets the settingsChanged flag to True."""
        nonlocal settingsChanged
        settingsChanged = True

    def resetSettingsChanged():
        """Sets the settingsChanged flag to False."""
        nonlocal settingsChanged
        settingsChanged = False

    def exit_settings():
        """Exit the settings screen with confirmation if settings are changed."""
        assert state.gui is not None
        if (
            settingsChanged  # or treeModel.hasChildren()
        ):  # Check for drag-and-drop changes
            reply = QMessageBox.question(
                mainWindow(),
                "Einstellungen verlassen",
                "Sind Sie sicher, dass Sie ohne Speichern verlassen wollen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                resetSettingsChanged()
                closeSettings()
                state.gui.inputBar.text.setFocus()
            else:
                return
        else:
            closeSettings()
            state.gui.inputBar.text.setFocus()

    # --- Menu Layout (Back Button) ---
    settingmenuLayout = QHBoxLayout()
    returnButton = QPushButton("🏠")
    returnButton.setToolTip("Rückkehr zum Hauptmenü")
    returnButton.clicked.connect(exit_settings)
    settingmenuLayout.addWidget(returnButton)

    # Spacer to align return button to the left
    horizontalSpacer = QSpacerItem(
        20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
    )
    settingmenuLayout.addItem(horizontalSpacer)
    settingsLayout.addLayout(settingmenuLayout)

    # --- Heading ---
    headingLabel = QLabel("Einstellungen")
    headingLabel.setStyleSheet("font-size: 24px; font-weight: bold;")
    settingsLayout.addWidget(headingLabel)

    # --- Theme Selection ---
    themeGroup = QGroupBox("Einheitensystem auswählen")
    themeLayout = QHBoxLayout()
    lightRadio = QRadioButton("Metrisch")
    darkRadio = QRadioButton("Imperial")
    if tempSettings.unitSystem == "Metrisch":
        lightRadio.setChecked(True)
    else:
        darkRadio.setChecked(True)
    themeLayout.addWidget(lightRadio)
    themeLayout.addWidget(darkRadio)
    themeGroup.setLayout(themeLayout)
    settingsLayout.addWidget(themeGroup)
    lightRadio.toggled.connect(setSettingsChanged)
    darkRadio.toggled.connect(setSettingsChanged)

    # --- Language Selection ---
    languagLabel = QLabel("Sprache:")
    languageCombo = QComboBox()
    languageCombo.addItems(["English", "Spanish", "French", "German"])
    languageCombo.setCurrentText(tempSettings.language)
    settingsLayout.addWidget(languagLabel)
    settingsLayout.addWidget(languageCombo)
    languageCombo.currentTextChanged.connect(
        lambda: setattr(tempSettings, "language", languageCombo.currentText())
        or setSettingsChanged()
    )

    # --- File Path Selection ---
    fileLayout = QHBoxLayout()
    filelabel = QLabel("Datei-Pfad:")
    fileLayout.addWidget(filelabel)
    filePathDisplay = QLineEdit(f"{tempSettings.filePath}")
    fileLayout.addWidget(filePathDisplay)
    fileButton = QPushButton("Datei auswählen")
    fileButton.clicked.connect(lambda: selectExeclFile(filePathDisplay))
    fileLayout.addWidget(fileButton)
    settingsLayout.addLayout(fileLayout)
    filePathDisplay.textChanged.connect(setSettingsChanged)

    # --- Tree View for Storage Locations ---
    storageLocations = QLabel("Lagerorte")
    storageLocations.setStyleSheet("font-weight: bold; font-size: 20px")
    settingsLayout.addWidget(storageLocations)

    locationWidget = createLocationEditor(state)
    settingsLayout.addWidget(locationWidget)

    settingsLayout.addItem(
        QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
    )

    # --- Save and Cancel Buttons ---
    settingsaveLayout = QHBoxLayout()
    horizontalSpacer = QSpacerItem(
        20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
    )
    settingsaveLayout.addItem(horizontalSpacer)
    settingsLayout.addLayout(settingsaveLayout)
    cancelButton = QPushButton("Abbrechen")
    settingsaveLayout.addWidget(cancelButton)
    saveButton = QPushButton("Speichern")
    settingsaveLayout.addWidget(saveButton)

    def saveSettings():
        """Saves the settings to the configuration file."""
        tempSettings.unitSystem = "Metrisch" if lightRadio.isChecked() else "Imperial"
        tempSettings.language = languageCombo.currentText()

        # Check if the file path exists
        if not os.path.exists(filePathDisplay.text()):
            filePathDisplay.setStyleSheet("QLineEdit { border: 2px solid red; }")
            QMessageBox.information(settingsWidget, "Error", "Datei existiert nicht.")
            return
        filePath = filePathDisplay.text()

        # Reload data from the file and save the configuration
        try:
            db.reloadFromFile(state.data, filePath)
        except Exception:
            filePathDisplay.setStyleSheet("QLineEdit { border: 2px solid red; }")
            QMessageBox.information(
                settingsWidget, "Error", "Datei konnte nicht geladen werden."
            )
            return

        # Update storage locations
        # tempSettings.locations = getStorageLocations()

        # Save the updated settings
        state.settings = tempSettings
        writeSettings(state.settings)
        print("Settings saved successfully.")
        QMessageBox.information(
            mainWindow(), "Erfolg", "Einstellungen erfolgreich gespeichert!"
        )
        resetSettingsChanged()
        closeSettings()

    saveButton.clicked.connect(saveSettings)

    # --- Cancel Function ---
    def cancelSettings():
        """Cancels the settings and returns to the main menu."""
        assert state.gui is not None
        if settingsChanged:
            reply: QMessageBox.StandardButton = QMessageBox.question(
                mainWindow(),
                "Verlassen bestätigen",
                "Sind Sie sicher, dass Sie ohne Speichern verlassen wollen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            assert type(reply) == QMessageBox.StandardButton
            if reply == QMessageBox.StandardButton.Yes:
                resetSettingsChanged()
                closeSettings()

            else:
                return
        else:
            closeSettings()

    cancelButton.clicked.connect(cancelSettings)

    return settingsWidget
