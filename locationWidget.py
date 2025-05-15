from typing import Callable, Literal, Sequence
from PySide6.QtWidgets import (
    QTreeView,
    QMessageBox,
    QInputDialog,
    QHBoxLayout,
    QCheckBox,
    QSpacerItem,
    QSizePolicy,
    QAbstractItemView,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QByteArray,
    QIODevice,
    QDataStream,
    QMimeData,
    QPersistentModelIndex,
)
from location import getChildren, getLocation, isDuplicateNameWithinParent, keepTopParents, newLocation, sortLocations
from state import *
import db


class CustomTreeModel(QStandardItemModel):
    def __init__(self, state: State, onUpdate: Callable[[], None]):
        super().__init__()
        self.onUpdate = onUpdate
        self.state = state

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction

    def mimeTypes(self):
        return ["application/x-qstandarditemmodeldatalist"]

    def mimeData(self, indexes: Sequence[QModelIndex]):
        mimeData = super().mimeData(indexes)
        encodedData = QByteArray()
        stream = QDataStream(encodedData, QIODevice.OpenModeFlag.WriteOnly)
        for index in indexes:
            if index.isValid():
                item = self.itemFromIndex(index)
                stream.writeQString(item.data(Qt.ItemDataRole.UserRole))
        mimeData.setData("application/x-qstandarditemmodeldatalist", encodedData)
        return mimeData

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex,
    ):
        if action == Qt.DropAction.IgnoreAction:
            return True
        if not data.hasFormat("application/x-qstandarditemmodeldatalist"):
            return False
        if column > 0:
            return False

        if parent.isValid():
            parentLocation = getLocationFromQIndex(self.state.data.locations, self, parent)
        else:
            parentLocation = None
        encodedData = data.data("application/x-qstandarditemmodeldatalist")
        stream = QDataStream(encodedData, QIODevice.OpenModeFlag.ReadOnly)
        locationIdsToMove: list[str] = []

        while not stream.atEnd():
            id: str = stream.readQString()
            location = getLocation(self.state.data.locations, id)
            locationIdsToMove.append(location.id)
            if location.parent is not parentLocation and isDuplicateNameWithinParent(
                self.state.data.locations, location.name, parentLocation
            ):
                QMessageBox.warning(
                    mainWindow(),
                    "Duplizierung",
                    "Der gleicher Name exisitiert bereits an der Ziel position",
                )
                return False


        # Reloading from File refreshes all references. 
        # After that line references to location object are invalide
        # They need to be retrieved by their ids
        db.reloadFromFile(self.state.data, self.state.settings.filePath)
        locationsToMove = [getLocation(self.state.data.locations, id) for id in locationIdsToMove]
        locationsToMove = keepTopParents(self.state.data.locations, locationsToMove)
        for location in locationsToMove:
            location.parent = None if parentLocation is None else parentLocation.id
        db.saveToExel(self.state.data, self.state.settings.filePath)
        if parentLocation:
            getLocation(self.state.data.locations, parentLocation.id).expanded = True
        self.onUpdate()
        return True

    def flags(self, index: QModelIndex | QPersistentModelIndex):
        defaultFlags = super().flags(index)
        if index.isValid():
            return (
                Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
                | defaultFlags
            )
        else:
            return Qt.ItemFlag.ItemIsDropEnabled | defaultFlags

def getLocationFromQIndex(locations: list[Location], model: QStandardItemModel, index: QModelIndex | QPersistentModelIndex) -> Location:
    item = model.itemFromIndex(index)
    locationId = item.data(Qt.ItemDataRole.UserRole)
    return getLocation(locations, locationId)


def createLocationTree(
    parentItem: QStandardItem | QStandardItemModel,
    locations: list[Location],
    parent: Location | None = None
):
    """Recursive function to add sub-locations to the tree view."""
    for location in getChildren(locations, parent):
        locationItem = QStandardItem(location.name)
        locationItem.setEditable(False)
        # Store the location id as hidden data
        locationItem.setData(location.id, Qt.ItemDataRole.UserRole)
        parentItem.appendRow(locationItem)
        createLocationTree(locationItem, locations, location)


def updateTreeView(locations: list[Location], treeView: QTreeView, expandLock: Lock):
    """Function to update the tree view with storage locations."""
    locations = sortLocations(locations)

    treeModel = treeView.model()
    assert isinstance(treeModel, QStandardItemModel)
    treeModel.removeRows(0, treeModel.rowCount())  # Clear model

    # Add storage locations as a hierarchical structure (nested)
    createLocationTree(treeModel, locations)
    with expandLock:
        restoreExpandedState(locations, treeView, treeModel)


def captureExpandedState(
    locations: list[Location],
    treeView: QTreeView,
    model: QStandardItemModel,
    lock: Lock,
    parent: QModelIndex = QModelIndex(),
):
    if lock.locked:
        return
    for row in range(treeView.model().rowCount(parent)):
        index = model.index(row, 0, parent)
        location = getLocationFromQIndex(locations, model, index)
        location.expanded = treeView.isExpanded(index)
        if model.hasChildren(index):
            captureExpandedState(locations, treeView, model,lock, index)


def restoreExpandedState(
    locations: list[Location],
    treeView: QTreeView,
    model: QStandardItemModel,
    parent: QModelIndex = QModelIndex(),
):
    for row in range(model.rowCount(parent)):
        index = model.index(row, 0, parent)
        location = getLocationFromQIndex(locations, model, index)
        if location.expanded:
            treeView.expand(index)
        if model.hasChildren(index):
            restoreExpandedState(locations, treeView, model, index)


def setMultiSelectionMode(treeView: QTreeView, enabled: bool):
    if enabled:
        treeView.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    else:
        treeView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)


def createLocationPicker(
    state: State, onPicked: Callable[[Location | None], None]
) -> QWidget:
    return createTreeView(state, "picker", onPicked)


def createLocationEditor(state: State) -> QWidget:
    return createTreeView(state, "editor")


def createTreeView(
    state: State,
    mode: Literal["editor", "picker"],
    onPicked: Callable[[Location | None], None] | None = None,
) -> QWidget:
    locationWidget = QWidget()
    locationLayout = QVBoxLayout()
    locationWidget.setLayout(locationLayout)

    treeView = QTreeView()
    treeModel = CustomTreeModel(state, lambda: updateTreeView(state.data.locations, treeView, expandLock))
    treeView.setModel(treeModel)
    # Header for Tree View
    treeView.setAnimated(True)
    treeView.setColumnHidden(0, True)
    treeView.setHeaderHidden(True)

    if mode == "editor":
        treeView.setDragEnabled(True)
        treeView.setAcceptDrops(True)
        treeView.setDropIndicatorShown(True)
    locationLayout.addWidget(treeView)

    expandLock = Lock()

    buttonLayout = QHBoxLayout()
    if mode == "editor":
        addButton = QPushButton("Hinzufügen")
        addButton.setToolTip("Neuer Lagerort anlegen")
        buttonLayout.addWidget(addButton)

        renameButton = QPushButton("Unbenennen")
        renameButton.setToolTip("Ausgewählter Lagerort umbenennen")
        buttonLayout.addWidget(renameButton)

        deleteButton = QPushButton("Löschen")
        deleteButton.setToolTip("Ausgewählte Lagerorte löschen")
        buttonLayout.addWidget(deleteButton)

        # --- Multi-Selection Mode Checkbox ---
        multiSelectCheckbox = QCheckBox("Multi-selection auswählen")
        multiSelectCheckbox.setChecked(False)  # Default to extended selection
        multiSelectCheckbox.setToolTip("Shortcut: Ctrl + Click")
        buttonLayout.addWidget(multiSelectCheckbox)

        def onAddNewLocation():
            location = getCurrentSelectedLocation(state.data.locations, treeView)
            newName, ok = QInputDialog.getText(
                locationWidget,
                "Ort hinzufürgen",
                "Neuer Name:",
            )
            if not ok or newName == "":
                return
            if isDuplicateNameWithinParent(state.data.locations, newName, location):
                QMessageBox.warning(
                    locationWidget, "Fehler", "Der gleicher Name exisitiert bereits"
                )
                return
            if location is None:
                db.addLocation(state, newLocation(newName, None))
            else:
                db.addLocation(state, newLocation(newName, location.id))
            updateTreeView(state.data.locations, treeView, expandLock)

        addButton.clicked.connect(onAddNewLocation)

        def onDeleteLocation():
            location = getCurrentSelectedLocation(state.data.locations, treeView)
            if location is None:
                return
            db.removeLocation(state, location)
            updateTreeView(state.data.locations, treeView, expandLock)

        deleteButton.clicked.connect(onDeleteLocation)

        def onRenameLocation():
            locations = state.data.locations
            location = getCurrentSelectedLocation(state.data.locations, treeView)
            if location is None:
                return
            newName, ok = QInputDialog.getText(
                locationWidget,
                "Rename Location",
                "New name:",
                text=location.name,
            )
            if not (ok and newName != "" and newName != location.name):
                return
            if isDuplicateNameWithinParent(locations, newName, location.parent):
                QMessageBox.warning(
                    locationWidget, "Error", "Name already exists on this level"
                )
                return
            db.renameLocation(state, location, newName)
            updateTreeView(state.data.locations, treeView, expandLock)

        renameButton.clicked.connect(onRenameLocation)

        multiSelectCheckbox.stateChanged.connect(setMultiSelectionMode)

    if mode == "picker":
        assert onPicked is not None
        buttonLayout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        selectButton = QPushButton("Auswählen")
        selectButton.setToolTip("Markierten Lagerorte auswählen")
        buttonLayout.addWidget(selectButton)

        def onSelect():
            selection = getCurrentSelectedLocation(state.data.locations, treeView)
            if selection:
                onPicked(selection)

        cancelButton = QPushButton("Abbrechen")
        buttonLayout.addWidget(cancelButton)

        selectButton.clicked.connect(onSelect)
        cancelButton.clicked.connect(lambda: onPicked(None))

    horizontalSpacer = QSpacerItem(
        20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
    )
    buttonLayout.addItem(horizontalSpacer)

    locationLayout.addLayout(buttonLayout)

    # --- Update Tree View with Nested Structure ---

    updateTreeView(state.data.locations, treeView, expandLock)

    treeView.expanded.connect(lambda: captureExpandedState(state.data.locations, treeView, treeModel, expandLock))
    treeView.collapsed.connect(lambda: captureExpandedState(state.data.locations, treeView, treeModel, expandLock))

    treeView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    return locationWidget


def getCurrentSelectedLocation(locations: list[Location],treeView: QTreeView) -> Location | None:
    indexes = treeView.selectedIndexes()
    if indexes:
        model = treeView.model()
        assert isinstance(model, QStandardItemModel)
        locationId = model.itemFromIndex(indexes[0]).data(Qt.ItemDataRole.UserRole)
        return getLocation(locations, locationId)


# def getNamesForCurrentSelection(treeView: QTreeView) -> list[str]:
#     indexes = treeView.selectedIndexes()
#     if indexes:
#         item = treeView.model().itemFromIndex(indexes[0])  # type: ignore
#         assert type(item) == QStandardItem  # type: ignore

#         # Get the full path of the selected item
#         path: list[str] = []
#         while item:
#             path.insert(0, item.text())
#             item = item.parent()
#         return path
#     return []
