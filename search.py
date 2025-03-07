# type: ignore
# Due to thefuzz not having type hints, types are ignored for the hole file

from typing import Callable
from PySide6.QtWidgets import QLineEdit, QScrollArea, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
import thefuzz
import thefuzz.process


import db

searchWidget = None


class SecondWindow(QWidget):
    def closeEvent(self, event):
        global searchWidget
        searchWidget = None


def showSearch(data: db.Data, addId: Callable[[int], None]):
    """
    Shows a search window to allow searching to given data.

    Takes a callback to handle the found/selected ids, that way the search can be flexibly used.

    Parameters
    ----------
    data : The data to be searched
    addId : The callback to handle the found/selected ids.
    """
    global searchWidget
    if searchWidget is None:
        # Create the main widget
        searchWidget = SecondWindow()
        searchLayout = QVBoxLayout(searchWidget)

        # Create a selection for the column
        # columnSelectorLayout = QHBoxLayout()
        # columnSelectorLayout.addWidget(QLabel("Column:"))
        # columnSelector = QComboBox()
        # columnSelector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # columnSelector.addItems(["Column 1", "Column 2", "Column 3"])
        # columnSelectorLayout.addWidget(columnSelector)
        # searchLayout.addLayout(columnSelectorLayout)

        # Create a scroll area
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create a widget to hold the entries
        entriesWidget = QWidget()
        entriesLayout = QVBoxLayout(entriesWidget)
        scrollArea.setWidget(entriesWidget)

        searchLayout.addWidget(scrollArea)

        # Search bar
        searchBarLayout = QHBoxLayout()
        searchBar = QLineEdit()
        searchBar.setPlaceholderText("Search...")
        searchBar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        searchBar.textChanged.connect(
            lambda: search(searchBar, entriesLayout, data, addId)
        )
        searchBarLayout.addWidget(searchBar)
        searchLayout.addLayout(searchBarLayout)

        # Set the main widget layout
        searchWidget.setLayout(searchLayout)
        searchWidget.setWindowTitle("Search (Experimental)")
        searchWidget.resize(400, 500)

        # Show the main widget
        searchWidget.show()
    else:
        searchWidget.raise_()


def search(
    searchBar: QLineEdit,
    entriesLayout: QVBoxLayout,
    data: db.Data,
    addId: Callable[[int], None],
):
    """
    Searches the given ``data`` for the given text in the ``searchBar``.

    Shows the results in the ``entriesLayout``.
    """
    def addIdCallback(id: int):
        def inner():
            addId(id)
        return inner
    strings = db.getSearchableStrings(data)
    searchText = searchBar.text()
    results = thefuzz.process.extract(searchText, strings, limit=10)

    clearLayout(entriesLayout)
    for result in results:
        (string, rate) = result
        [id, rest] = string.split(":", maxsplit=1)
        rest.strip()

        entryLayout = QHBoxLayout()
        label = QLabel(rest)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button = QPushButton("Add")
        button.clicked.connect(addIdCallback(int(id)))
        entryLayout.addWidget(label)
        entryLayout.addWidget(button)
        entriesLayout.addLayout(entryLayout)


def clearLayout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()
        else:
            clearLayout(item.layout())
            item.layout().deleteLater()
