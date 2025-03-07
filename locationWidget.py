from functools import cmp_to_key
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
from location import getLocation, isDuplicateNameWithinParent, keepTopParents, newLocation
from state import *


class CustomTreeModel(QStandardItemModel):
    def __init__(self, settings: Settings, onUpdate: Callable[[], None]):
        super().__init__()
        self.onUpdate = onUpdate
        self.settings = settings

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
            parentLocation = getLocationFromQIndex(self.settings.locations, self, parent)
        else:
            parentLocation = None
        encodedData = data.data("application/x-qstandarditemmodeldatalist")
        stream = QDataStream(encodedData, QIODevice.OpenModeFlag.ReadOnly)
        locationsToMove: list[Location] = []

        while not stream.atEnd():
            id: str = stream.readQString()
            location = getLocation(self.settings.locations, id)
            locationsToMove.append(location)
            if location.parent is not parentLocation and isDuplicateNameWithinParent(
                self.settings.locations, location.name, parentLocation
            ):
                QMessageBox.warning(
                    mainWindow(),
                    "Duplizierung",
                    "Der gleicher Name exisitiert bereits an der Ziel position",
                )
                return False

        locationsToMove = keepTopParents(locationsToMove)
        for location in locationsToMove:
            oldParent = location.parent
            location.parent = parentLocation
            if parentLocation is not None:
                parentLocation.children.append(location)
            else:
                self.settings.locations.append(location)

            if oldParent is not None:
                oldParent.children.remove(location)
            else:
                self.settings.locations.remove(location)

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
):
    """Recursive function to add sub-locations to the tree view."""
    for location in locations:
        locationItem = QStandardItem(location.name)
        locationItem.setEditable(False)
        # Store the location id as hidden data
        locationItem.setData(location.id, Qt.ItemDataRole.UserRole)
        parentItem.appendRow(locationItem)
        createLocationTree(locationItem, location.children)


# --- Sort Locations ---


def sortLocations(locations: list[Location]) -> list[Location]:
    """Sorts the locations by their name."""

    def sortComparator(x1: Location, x2: Location):
        return (x1.name.lower() > x2.name.lower()) - (x1.name.lower() < x2.name.lower())

    for section in locations:
        sortLocations(section.children)
        section.children = sorted(section.children, key=cmp_to_key(sortComparator))
    return sorted(locations, key=cmp_to_key(sortComparator))


def updateTreeView(settings: Settings, treeView: QTreeView, expandLock: Lock):
    """Function to update the tree view with storage locations."""
    settings.locations = sortLocations(settings.locations)

    treeModel = treeView.model()
    assert isinstance(treeModel, QStandardItemModel)
    treeModel.removeRows(0, treeModel.rowCount())  # Clear model

    # Add storage locations as a hierarchical structure (nested)
    createLocationTree(treeModel, settings.locations)
    with expandLock:
        restoreExpandedState(settings.locations, treeView, treeModel)


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
    settings: Settings, onPicked: Callable[[Location | None], None]
) -> QWidget:
    return createTreeView(settings, "picker", onPicked)


def createLocationEditor(settings: Settings) -> QWidget:
    return createTreeView(settings, "editor")


def createTreeView(
    settings: Settings,
    mode: Literal["editor", "picker"],
    onPicked: Callable[[Location | None], None] | None = None,
) -> QWidget:
    locationWidget = QWidget()
    locationLayout = QVBoxLayout()
    locationWidget.setLayout(locationLayout)

    treeView = QTreeView()
    treeModel = CustomTreeModel(settings, lambda: updateTreeView(settings, treeView, expandLock))
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
            location = getCurrentSelectedLocation(settings.locations, treeView)
            newName, ok = QInputDialog.getText(
                locationWidget,
                "Ort hinzufürgen",
                "Neuer Name:",
            )
            if not ok or newName == "":
                return
            if isDuplicateNameWithinParent(settings.locations, newName, location):
                QMessageBox.warning(
                    locationWidget, "Fehler", "Der gleicher Name exisitiert bereits"
                )
                return
            if location is None:
                settings.locations.append(newLocation(newName, None))
            else:
                location.children.append(newLocation(newName, location))
            updateTreeView(settings, treeView, expandLock)

        addButton.clicked.connect(onAddNewLocation)

        def onDeleteLocation():
            location = getCurrentSelectedLocation(settings.locations, treeView)
            if location is None:
                return
            parent = location.parent
            if parent is None:
                return
            parent.children.remove(location)
            updateTreeView(settings, treeView, expandLock)

        deleteButton.clicked.connect(onDeleteLocation)

        def onRenameLocation():
            locations = settings.locations
            location = getCurrentSelectedLocation(settings.locations, treeView)
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
            location.name = newName
            updateTreeView(settings, treeView, expandLock)

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
            selection = getCurrentSelectedLocation(settings.locations, treeView)
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

    updateTreeView(settings, treeView, expandLock)

    treeView.expanded.connect(lambda: captureExpandedState(settings.locations, treeView, treeModel, expandLock))
    treeView.collapsed.connect(lambda: captureExpandedState(settings.locations, treeView, treeModel, expandLock))

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
