from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFileDialog
from PySide6.QtGui import QIcon
import os

# CONSTANTS
ICON_SIZE = (24, 24)

class SearchDialog(QDialog):
    def __init__(self, parent=None, items=None):
        """
        Initialize the SearchDialog.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            items (list[str], optional): List of items to search from. Defaults to an empty list if None.
        """
        super().__init__(parent)
        self.items = items or []
        self.selected_index = None
        self.setupUI()

    def setupUI(self):
        """Setup the user interface for the dialog."""
        self.setWindowTitle("Search Task")
        layout = QVBoxLayout(self)

        # Create and set up the search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search task...")
        self.search_bar.textChanged.connect(self.filterTasks)
        layout.addWidget(self.search_bar)

        # Create and set up the list widget to display tasks
        self.list_widget = QListWidget(self)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.populateTaskList(self.items)
        layout.addWidget(self.list_widget)

        # Create and set up the select button
        self.select_btn = QPushButton("Select Task", self)
        self.select_btn.clicked.connect(self.selectTask)
        layout.addWidget(self.select_btn)

    def populateTaskList(self, tasks):
        """
        Populate the list widget with the provided tasks.

        Args:
            tasks (list[str]): List of tasks to display.
        """
        self.list_widget.clear()
        self.list_widget.addItems(tasks)

    def filterTasks(self):
        """Filter the tasks in the list based on the search text."""
        search_text = self.search_bar.text().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(search_text not in item.text().lower())

    def getSelected(self):
        """
        Return the index of the selected item.

        Returns:
            int or None: Index of the selected item, or None if no item is selected.
        """
        return self.selected_index

    def selectTask(self):
        """Handle the task selection and close the dialog."""
        selected_index = self.list_widget.currentRow()
        if selected_index != -1:
            self.selected_index = selected_index
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a task from the list.")

class FieldSearchBox(QWidget):
    item_selected = Signal(int)

    def __init__(self, item_list=None, parent=None):
        """
        Initialize the FieldSearchBox.

        Args:
            item_list (list[str], optional): List of items for the search box. Defaults to an empty list if None.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.items = list(item_list) if item_list is not None else []
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface for the search box."""
        layout = QHBoxLayout(self)
        
        # Create and set up the item field
        self.item_field = QLineEdit(self)
        layout.addWidget(self.item_field)

        # Create and set up the search button
        self.search_btn = QPushButton(self)
        self.search_btn.setIcon(QIcon("./resources/search.png"))
        self.search_btn.setFixedSize(*ICON_SIZE)
        self.search_btn.clicked.connect(self.show_search_box)
        layout.addWidget(self.search_btn)
        
        layout.setContentsMargins(0, 0, 0, 0)

    def disableSearchBox(self):
        """Disable the search box feature."""
        self.search_btn.setEnabled(False)
        self.search_btn.setVisible(False)

    def enableSearchBox(self):
        """Enable the search box feature."""
        self.search_btn.setEnabled(True)
        self.search_btn.setVisible(True)

    def setItemList(self, items):
        """
        Set the list of items for the search box.

        Args:
            items (list[str]): List of items to search from.
        """
        self.items = items

    def text(self):
        """
        Return the current text from the item field.

        Returns:
            str: The current text in the item field.
        """
        return self.item_field.text()

    def clear(self):
        """Clear the text from the item field."""
        self.item_field.clear()

    def show_search_box(self):
        """Show the search dialog and handle item selection."""
        dialog = SearchDialog(self, self.items)
        if dialog.exec() == QDialog.Accepted:
            selected_idx = dialog.getSelected()
            if selected_idx is not None:
                self.item_field.setText(self.items[selected_idx])
                self.item_selected.emit(selected_idx)

class FieldBrowseFileBox(QWidget):
    path_seleted = Signal(int)

    def __init__(self, path:str, parent=None):
        super().__init__(parent)
        self.path = path
        self.setupUI()

    def setupUI(self):
        """Setup the user interface for the browse file box."""
        layout = QHBoxLayout(self)
        
        # Create and set up the item field
        self.path_field = QLineEdit(self)
        self.path_field.setText(self.path)
        layout.addWidget(self.path_field)

        # Create and set up the search button
        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedSize(*ICON_SIZE)
        self.browse_btn.clicked.connect(self.browsePathFile)
        layout.addWidget(self.browse_btn)
        
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def browsePathFile(self):
        """Open the dialog to select the path file"""
        file_path, _ = QFileDialog.getOpenFileName(self, 'Choose the database path', os.getcwd(), filter="Excel Files (*.xls *.xlsx);")
        if file_path and os.path.abspath(file_path) != os.path.abspath(self.path):
            print(f"Change the database path to: {file_path}")
            self.path= file_path
            self.path_field.setText(self.path)
    
    def getPath(self):
        return self.path