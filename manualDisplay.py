from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton, QInputDialog, QSpacerItem, QSizePolicy
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QShortcut, QKeySequence
from typing import Callable
from state import *

def createManualView(state: State, closeManual: Callable[[], None]):
    manual_file = open("assets/manual.md", "r", encoding='utf-8')
    manual_content = manual_file.read()
    manual_file.close()

    def exitManual():
        assert state.gui is not None
        closeManual()
        state.gui.inputBar.text.setFocus()

    def searchManual():
        search_term, ok = QInputDialog.getText(manual_widget, "Handbuch durchsuchen", "Gebe dein Suchbegriff ein:")
        if ok and search_term:
            cursor = manual_text.textCursor()
            format = QTextCharFormat()
            format.setBackground(QColor("yellow"))

            # Clear previous highlights
            cursor.setPosition(0)
            cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(QTextCharFormat())

            # Re-render the markdown content to preserve formatting
            manual_text.setMarkdown(manual_content)

            # Search and highlight
            cursor.setPosition(0)
            while True:
                cursor = manual_text.document().find(search_term, cursor)
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(format)

    # Create the main widget
    manual_widget = QWidget()
    layout = QVBoxLayout()

    # Create a horizontal layout for the buttons
    button_layout = QHBoxLayout()

    # Create a return button
    return_button = QPushButton("🏠")
    return_button.setToolTip("Zurück zum Hauptmenü")
    return_button.clicked.connect(exitManual)
    button_layout.addWidget(return_button)

    # Create a search button
    search_button = QPushButton("🔍")
    search_button.setToolTip("Handbuch durchsuchen")
    search_button.clicked.connect(searchManual)
    button_layout.addWidget(search_button)

    # Add the shortcut for Ctrl + F
    search_shortcut = QShortcut(QKeySequence("Ctrl+F"), manual_widget)
    search_shortcut.activated.connect(searchManual)

    # Create horizontal spacer for button layout
    horizontalSpacer = QSpacerItem(
        20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
    )
    button_layout.addItem(horizontalSpacer)


    # Add the button layout to the main layout
    layout.addLayout(button_layout)

    # Create a QTextEdit to display the manual content
    manual_text = QTextEdit()
    manual_text.setReadOnly(True)
    manual_text.setMarkdown(manual_content)

    # Add the QTextEdit to the layout
    layout.addWidget(manual_text)
    manual_widget.setLayout(layout)

    return manual_widget