from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, QDoubleValidator, QCloseEvent, QFont
from custom import FieldSearchBox, FieldBrowseFileBox
from task import add_new_task_item, load_task_list, edit_task_item, delete_task_item
from datetime import datetime
import sys
import os
import json

# Constants
USERNAME = "DeeDee2804"
WINDOW_TITLE = "Task Tracking"
WINDOW_HEIGHT = 100
WINDOW_WIDTH = 400
ICON_SIZE = (24, 24)
CONFIG_DATA = {}
CONFIG_DATA["database"] = "./Test.xlsx"
CONFIG_DATA["category"] = ["Category 1", "Category 2", "Category 3", "Category 4",
                           "Category 5", "Category 6", "Category 7", "Category 8",
                           "Category 9"]
CONFIG_DATA["assigner"] = ["Person 1", "Person 2", "Person 3", "Person 4",
                           "Person 5", "Person 6", "Person 7", "Person 8",
                           "Person 9"]
CONFIG_DATA["status"] = ["TO DO", "IN PROGRESS", "DONE", "BLOCK", "CANCELED"]
REASON_STATUS = ["BLOCK", "CANCELED"]
FIXED_FIELD_WIDTH = 200
BUTTON_HEIGHT = 40
BUTTON_WIDTH = 100
TASK_DATA_PATH = "./data.json"
BOSCHPURPLE_COLOR = "#9E2896"
BOSCHBLUE_COLOR = '#007BC0'
BOSCHTURQUOISE_COLOR = '#18837E'
BOSCHGRAY_COLOR = '#2E3033'
DIALOG_WAIT_TIME = 3000

class ComboxWithoutScrolling(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def wheelEvent(self, event):
        # Override wheel event to prevent scrolling
        event.ignore()

class ComboBoxEditor(QWidget):
    def __init__(self, field_name: str, option_list=None, parent=None):
        super().__init__(parent)
        self.name = field_name
        self.combo_box = self.createCombobox(option_list)
        self.edit_button = self.createEditButton()

        layout = QHBoxLayout()
        layout.addWidget(self.combo_box)
        layout.addWidget(self.edit_button)
        layout.addSpacerItem(QSpacerItem(40, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def createCombobox(self, options):
        combo_box = QComboBox()
        if options:
            combo_box.addItems(options)
        return combo_box

    def createEditButton(self):
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.open_editor_dialog)
        return edit_button

    def currentText(self):
        return self.combo_box.currentText()
    
    def selectOption(self, option):
        self.combo_box.setCurrentText(option)
        
    def clear(self):
        '''
        Reset the current option of combo box to the first option
        '''
        self.combo_box.setCurrentIndex(0)
        
    def open_editor_dialog(self):
        dialog = ComboBoxEditorDialog(self, self.combo_box, self.name)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            CONFIG_DATA[self.name] = [self.combo_box.itemText(i) for i in range(self.combo_box.count())]
            save_environment()
        else:
            print("Dialog rejected")

class ComboBoxEditorDialog(QDialog):
    def __init__(self, parent, combo_box: QComboBox, name: str):
        super().__init__(parent)
        self.combo_box = combo_box
        self.setWindowTitle(f"{name.title()} Edit")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.item_list = self.create_item_list()
        layout.addWidget(QLabel("Values:"))
        layout.addWidget(self.item_list)
        layout.addLayout(self.create_button_layout())
        self.setLayout(layout)

    def create_item_list(self):
        item_list = QListWidget()
        item_list.addItems([self.combo_box.itemText(i) for i in range(self.combo_box.count())])
        item_list.setStyleSheet("QListWidget { background-color: transparent; }")
        return item_list

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_button("Add", self.add_item))
        button_layout.addWidget(self.create_button("Delete", self.delete_item))
        button_layout.addWidget(self.create_button("Update", self.update_item))
        return button_layout

    def create_button(self, label, callback):
        button = QPushButton(label)
        button.setFixedSize(80, 30)
        button.clicked.connect(callback)
        return button

    def add_item(self):
        new_item, ok = QInputDialog.getText(self, "Add Item", "Enter new item:")
        if ok and new_item:
            self.combo_box.addItem(new_item)
            self.item_list.addItem(new_item)

    def delete_item(self):
        selected_items = self.item_list.selectedItems()
        if selected_items:
            reply = QMessageBox.question(self, "Delete Item", 
                                         "Are you sure you want to delete the selected item(s)?", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                for item in selected_items:
                    text = item.text()
                    index = self.combo_box.findText(text)
                    if index != -1:
                        self.combo_box.removeItem(index)
                    self.item_list.takeItem(self.item_list.row(item))

    def update_item(self):
        selected_items = self.item_list.selectedItems()
        if selected_items:
            current_item = selected_items[0]
            new_item, ok = QInputDialog.getText(self, "Update Item", "Enter new item name:", text=current_item.text())
            if ok and new_item:
                index = self.combo_box.findText(current_item.text())
                if index != -1:
                    self.combo_box.setItemText(index, new_item)
                    current_item.setText(new_item)

    def closeEvent(self, event: QEvent):
        # Handle the close event
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Do you want to save your change?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()  # Allow the dialog to close
        else:
            self.reject()

class ReasonInputDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Update the Reason")
        self.data = data
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout()
        header_label = QLabel("<b>Change Status</b>")
        header_label.setStyleSheet("font-size: 18px")
        layout.addWidget(header_label, alignment=Qt.AlignmentFlag.AlignCenter)
        form_layout =QFormLayout()
        form_layout.addRow("<b>Category:</b>", QLabel(self.data['category']))
        form_layout.addRow("<b>Task:</b>", QLabel(self.data['task']))
        form_layout.addRow("<b>Status changed:</b>", QLabel(self.data['status']))
        self.reason = QPlainTextEdit()
        row_height = self.reason.fontMetrics().height()
        padding = self.reason.frameWidth() * 2  # Adjust for the frame's padding
        self.reason.setFixedHeight(3 * row_height + padding)
        form_layout.addRow("<b>Reason:</b>", self.reason)
        layout.addLayout(form_layout)
        submit_btn = QPushButton("SUBMIT")
        submit_btn.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        submit_btn.clicked.connect(self.submitChange)
        layout.addWidget(submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
    
    def getReason(self):
        return self.reason.toPlainText()
    
    def closeEvent(self, event):
        if self.reason.toPlainText() != "":
            self.accept()
        else:
            self.reject()
            
    def submitChange(self):
        if self.reason.toPlainText() != "":
            self.accept()
        else:
            QMessageBox.warning(self, "No reason", "Please input a reason for your change.")

class DateSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setupUI()

    def setupUI(self):
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setSelectedDate(QDate.currentDate())

        layout = QVBoxLayout()
        layout.addWidget(self.calendar)
        self.setLayout(layout)

        self.calendar.clicked.connect(self.select_date)

    def select_date(self, date):
        self.selected_date = date
        self.accept()

    def get_date(self) -> QDate:
        return self.selected_date

class DateSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        self.date_input = self.create_date_input()
        self.calendar_button = self.create_calendar_button()

        layout.addWidget(self.date_input)
        layout.addWidget(self.calendar_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def create_date_input(self):
        date_input = QLineEdit()
        date_input.setPlaceholderText("Select a date...")
        date_input.setReadOnly(True)
        return date_input

    def text(self):
        return self.date_input.text()
    
    def setText(self, text):
        self.date_input.setText(text)
        
    def clear(self):
        self.date_input.clear()
    
    def create_calendar_button(self):
        calendar_button = QPushButton()
        calendar_button.setIcon(QIcon("./resources/calendar.png"))
        calendar_button.setFixedSize(24, 24)
        calendar_button.clicked.connect(self.show_calendar)
        return calendar_button

    def show_calendar(self):
        dialog = DateSelectorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = dialog.get_date().toString("yyyy-MM-dd")
            self.date_input.setText(selected_date)

class StartPage(QWidget):
    
    def __init__(self, parent: QMainWindow=None):
        super().__init__(parent)
        self.parent = parent
        #TODO: Add validation for the database
        self.tasks = load_task_list(CONFIG_DATA['database'])
        self.create_page = CreateTaskPage()
        self.create_page.task_created.connect(self.updateTaskList)
        self.update_page = UpdateTaskPage(self.tasks)
        self.setting_page = SettingPage()
        self.setting_page.configuration_changed.connect(self.updateDatabase)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedSize(600, 200)
        # Add heading label
        heading_label = QLabel("<b>Task Tracking</b>")
        heading_label.setStyleSheet("font-size: 16pt")
        self.layout.addWidget(heading_label, stretch=-1,alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Add setting button that place on top of heading label to enable change the database
        self.setting_btn = QPushButton(self)
        self.setting_btn.setIcon(QIcon("./resources/settings.png"))
        self.setting_btn.setGeometry(560, 10, 30, 30)
        self.setting_btn.raise_()
        self.setting_btn.clicked.connect(self.showSettingPage)
        
        # Add welcome note
        self.layout.addWidget(QLabel(f"Welcome {USERNAME}, wish you have a nice day!"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(QLabel("What would you like to do?"), alignment=Qt.AlignmentFlag.AlignCenter)

        # Add the button box
        btn_box = QGridLayout()
        self.create_task_btn = QPushButton("CREATE NEW TASK")
        self.create_task_btn.setFixedHeight(BUTTON_HEIGHT)
        self.create_task_btn.clicked.connect(self.showCreatePage)
        self.create_task_btn.setStyleSheet(f"background-color: {BOSCHPURPLE_COLOR}; color: white")
        
        self.update_task_btn = QPushButton("UPDATE TASK")
        self.update_task_btn.setFixedHeight(BUTTON_HEIGHT)
        self.update_task_btn.clicked.connect(self.showUpdatePage)
        self.update_task_btn.setStyleSheet(f"background-color: {BOSCHBLUE_COLOR}; color: white")
        self.update_task_btn.clicked.connect(self.update_page.disableFieldsExceptTask)
        
        self.today_task_btn = QPushButton("TODAY TASK")
        self.today_task_btn.setFixedHeight(BUTTON_HEIGHT)
        self.today_task_btn.setStyleSheet(f"background-color: {BOSCHTURQUOISE_COLOR}; color: white")
        self.today_task_btn.clicked.connect(self.showTodayPage)
        
        self.raw_data_btn = QPushButton("RAW DATA")
        self.raw_data_btn.setFixedHeight(BUTTON_HEIGHT)
        self.raw_data_btn.setStyleSheet(f"background-color: {BOSCHGRAY_COLOR}; color: white")
        self.raw_data_btn.clicked.connect(self.openExcelFile)

        btn_box.addWidget(self.create_task_btn, 0, 0)
        btn_box.addWidget(self.update_task_btn, 0, 1)
        btn_box.addWidget(self.today_task_btn, 1, 0)
        btn_box.addWidget(self.raw_data_btn, 1, 1)
        
        self.layout.addLayout(btn_box, stretch=1)
    
    def showSettingPage(self):
        self.setting_page.show()
        
    def updateDatabase(self):
        self.tasks = load_task_list(CONFIG_DATA['database'])
        self.update_page.updateSearchBox(self.tasks)
        
    def openExcelFile(self):
        os.startfile(os.path.abspath(CONFIG_DATA['database']))
        
    def showCreatePage(self):
        self.create_page.show()

    def showTodayPage(self):
        self.today_page = TodayTaskPage(self.tasks)
        self.today_page.show()
    
    def updateTaskList(self, task):
        self.tasks.append(task)
        self.update_page.updateSearchBox(self.tasks)
        
    def showUpdatePage(self):
        self.update_page.show()
          
class BaseTaskPage(QWidget):
    """Base class for CreateTaskPage and UpdateTaskPage, containing common fields and logic."""
    layout: QVBoxLayout
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.fields: list[QWidget] = []
        self.setupUI(title)
    
    def setupUI(self, title: str):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setWindowTitle(title)
        heading_label = QLabel(f"<b>{title}</b>")
        heading_label.setStyleSheet("font-size: 12pt")
        self.layout.addWidget(heading_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        form_layout = QFormLayout()
        self.do_date_field = DateSelector()
        self.category_field = ComboBoxEditor("category", CONFIG_DATA["category"])
        self.task_field = FieldSearchBox()
        self.description_field = QPlainTextEdit()
        self.assigner_field = ComboBoxEditor("assigner", CONFIG_DATA["assigner"])
        self.deadline_field = DateSelector()
        self.status_field = ComboBoxEditor("status", CONFIG_DATA["status"])
        self.estimated_field = QLineEdit()
        double_validator = QDoubleValidator(0.0, 1000.0, 2, self)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)  # Ensure standard float notation

        # Set validators for numeric input fields
        self.estimated_field.setValidator(double_validator)
        
        # Set a fixed width for DateSelector fields to match QLineEdit fields
        fixed_width = 200
        self.do_date_field.setFixedWidth(fixed_width)
        self.deadline_field.setFixedWidth(fixed_width)
        
        # Add fields to the form layout
        form_layout.addRow(QLabel("Do Date *"), self.do_date_field)
        form_layout.addRow(QLabel("Category task *"), self.category_field)
        form_layout.addRow(QLabel("Task *"), self.task_field)
        form_layout.addRow(QLabel("Description"), self.description_field)
        form_layout.addRow(QLabel("Assigner *"), self.assigner_field)
        form_layout.addRow(QLabel("Deadline"), self.deadline_field)
        form_layout.addRow(QLabel("Status *"), self.status_field)
        form_layout.addRow(QLabel("Estimate hour *"), self.estimated_field)
        
        self.layout.addLayout(form_layout)

    def enableSearchBox(self):
        self.task_field.enableSearchBox()
    
    def updateSearchBox(self, item_list):
        task_list = [item['task'] for item in item_list]
        self.task_field.setItemList(task_list)
        
    def disableSearchBox(self):
        self.task_field.disableSearchBox()
        
    def collectData(self):
        """Method to collect common data from the form."""
        data = {
            "do_date": self.do_date_field.text(),
            "category": self.category_field.currentText(),
            "task": self.task_field.text(),
            "description": self.description_field.toPlainText(),
            "assigner": self.assigner_field.currentText(),
            "deadline": self.deadline_field.text(),
            "status": self.status_field.currentText(),
            "estimated_hours": self.estimated_field.text(),
            "spent_hours": "",
            "result": "",
            "reason": ""
        }
        return data

    def cleanAllFields(self):
        """Method to clear all data"""
        self.do_date_field.clear()
        self.category_field.clear()
        self.task_field.clear()
        self.description_field.clear()
        self.assigner_field.clear()
        self.deadline_field.clear()
        self.status_field.clear()
        self.estimated_field.clear()
    
    def isValidated(self) -> bool:
        """Validate if all mandatory field is provided"""
        is_valid = self.do_date_field.text() != ""\
            and self.task_field.text() != ""\
            and self.estimated_field.text() != ""
        return is_valid

    def triggerInfoMessage(self, title, text):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(text)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.show()
        QTimer.singleShot(DIALOG_WAIT_TIME, dialog.close)
        
# Specific class for creating tasks
class CreateTaskPage(BaseTaskPage):
    task_created = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__("Create New Task", parent)
        self.setupCreateButton()
        self.disableSearchBox()
    
    def setupCreateButton(self):
        """Sets up the Create button and its behavior."""
        self.create_btn = QPushButton("CREATE")
        self.create_btn.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.create_btn.setStyleSheet(f'background-color: {BOSCHPURPLE_COLOR}; color: white; font-weight: bold;')
        self.create_btn.clicked.connect(self.create_task)
        self.layout.addWidget(self.create_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def create_task(self):
        """Collect data and create the task."""
        if self.isValidated() == True:
            task_data = self.collectData()
            add_new_task_item(CONFIG_DATA['database'], task_data)
            print("Creating Task:", task_data)
            self.cleanAllFields()
            self.task_created.emit(task_data)
            self.triggerInfoMessage('Success', 'Task is created successfully!')

        else:
            QMessageBox.warning(self, "Lack of information", "Please input all the mandatory.")
        # self.hide()
        
    def closeEvent(self, event: QCloseEvent):
        """Override closeEvent to clear all fields when closing the page."""
        self.cleanAllFields()
        event.accept() 

# Specific class for updating tasks
class UpdateTaskPage(BaseTaskPage):
    def __init__(self, tasks=None, parent=None):
        super().__init__("Update Task", parent)
        self.setupAdditionalFields()
        self.setupUpdateButton()
        self.tasks = tasks if tasks else []
        self.current_idx = -1
        self.enableSearchBox()
        self.updateSearchBox(self.tasks)
        self.task_field.item_selected.connect(self.enableFieldsForEditing)
        self.task_field.item_selected.connect(self.loadTaskItem)
        self.setupConditionalFields()
        
    
    def setupAdditionalFields(self):
        """Sets up the additional fields specific to updating a task."""
        form_layout: QFormLayout = self.layout.itemAt(1)  # Get the existing form layout
        
        self.spent_field = QLineEdit()
        self.result_field = QPlainTextEdit()
        double_validator = QDoubleValidator(0.0, 1000.0, 2, self)
        self.spent_field.setValidator(double_validator)
        
        # Add additional fields for updating a task
        form_layout.addRow(QLabel("Spent hour"), self.spent_field)
        form_layout.addRow(QLabel("Result"), self.result_field)

        # Create the block reason field (hidden by default)
        self.reason_label = QLabel("Reason *")
        self.reason_field = QLineEdit()
        form_layout.addRow(self.reason_label, self.reason_field)
        
        # Initially hide the Block Reason field
        self.reason_label.hide()
        self.reason_field.hide()
    
    def loadTaskItem(self, task_index):
        """Fill all the field with the task at the corresponding index"""
        self.current_idx = task_index
        current_task = self.tasks[task_index]
        self.do_date_field.setText(current_task["do_date"])
        self.category_field.selectOption(current_task['category'])
        self.description_field.setPlainText(current_task['description'])
        self.assigner_field.selectOption(current_task['assigner'])
        self.deadline_field.setText(current_task['deadline'])
        self.status_field.selectOption(current_task['status'])
        self.estimated_field.setText(str(current_task['estimated_hours']))
        self.spent_field.setText(str(current_task['spent_hours']))
        self.result_field.setPlainText(current_task['result'])
        self.reason_field.setText(current_task['reason'])
    
    def cleanAllFields(self):
        super().cleanAllFields()
        self.current_idx = -1
        self.spent_field.clear()
        self.result_field.clear()
        self.reason_field.clear()
        
    def closeEvent(self, event: QCloseEvent):
        """Override closeEvent to clear all fields when closing the page."""
        self.cleanAllFields()
        event.accept() 
        
    def setupUpdateButton(self):
        """Sets up the Update button and its behavior."""
        button_box = QHBoxLayout()
        self.update_btn = QPushButton("UPDATE")
        self.update_btn.setStyleSheet(f"background-color: {BOSCHBLUE_COLOR};color: white; font-weight: bold;")
        self.update_btn.setFixedHeight(BUTTON_HEIGHT)
        self.update_btn.clicked.connect(self.updateTask)
        button_box.addWidget(self.update_btn)
        self.delete_btn = QPushButton("DELETE")
        self.delete_btn.setStyleSheet(f"background-color: {BOSCHPURPLE_COLOR};color: white; font-weight: bold;")
        self.delete_btn.setFixedHeight(BUTTON_HEIGHT)
        self.delete_btn.clicked.connect(self.deleteTask)
        button_box.addWidget(self.delete_btn)
        self.layout.addLayout(button_box)
        
    def disableFieldsExceptTask(self):
        """Disable all fields except the task field for task searching."""
        self.do_date_field.setEnabled(False)
        self.category_field.setEnabled(False)
        self.description_field.setEnabled(False)
        self.assigner_field.setEnabled(False)
        self.deadline_field.setEnabled(False)
        self.status_field.setEnabled(False)
        self.estimated_field.setEnabled(False)
        self.spent_field.setEnabled(False)
        self.result_field.setEnabled(False)
        self.reason_field.setEnabled(False)

        # Enable the task field
        self.task_field.setEnabled(True)

    def enableFieldsForEditing(self):
        """Enable all fields after a task has been selected."""
        self.do_date_field.setEnabled(True)
        self.category_field.setEnabled(True)
        self.description_field.setEnabled(True)
        self.assigner_field.setEnabled(True)
        self.deadline_field.setEnabled(True)
        self.status_field.setEnabled(True)
        self.estimated_field.setEnabled(True)
        self.spent_field.setEnabled(True)
        self.result_field.setEnabled(True)
        self.reason_field.setEnabled(True)
        
    def setupConditionalFields(self):
        """Setup logic to show/hide the Block Reason field based on the status."""
        self.status_field.combo_box.currentTextChanged.connect(self.toggleReasonField)

    def toggleReasonField(self):
        """Show or hide the Block Reason field based on the selected status."""
        if self.status_field.currentText() in REASON_STATUS:
            self.reason_label.show()
            self.reason_field.show()
        else:
            self.reason_label.hide()
            self.reason_field.hide()
    
    def isValidated(self) -> bool:
        is_valid = super().isValidated()
        if self.status_field.currentText() == "DONE":
            is_valid = is_valid and (self.spent_field.text() != "")
        if self.status_field.currentText() in REASON_STATUS:
            is_valid = is_valid and (self.reason_field.text() != "")
        return is_valid
    
    def updateTask(self):
        """Collect data and update the task."""
        task_data = self.collectData()
        task_data["spent_hours"] = self.spent_field.text()
        task_data["result"] = self.result_field.toPlainText()
        if self.status_field.currentText() in REASON_STATUS:
            task_data["reason"] = self.reason_field.text()
        
        # Check if the task exists and all mandatory fields are provided
        if self.current_idx != -1 and self.isValidated():
            print("Updating Task:", task_data)
            edit_task_item(CONFIG_DATA['database'], self.current_idx, task_data)
            self.tasks[self.current_idx] = task_data
            self.updateSearchBox(self.tasks)
            self.cleanAllFields()
            self.triggerInfoMessage("Success", "Task is updated succesfully!")
            self.disableFieldsExceptTask()
        else:
            QMessageBox.warning(self, "Lack of information", "All mandatory fields must be provided!")
            
    def deleteTask(self):
        """Delete the current chosen task"""
        if self.current_idx != -1:
            print("Deleting Task:", self.tasks[self.current_idx])
            delete_task_item(CONFIG_DATA['database'], self.current_idx)
            self.tasks.pop(self.current_idx)
            self.updateSearchBox(self.tasks)
            self.cleanAllFields()
            self.triggerInfoMessage("Success", "Task is deleted succesfully!")
            self.disableFieldsExceptTask()
        else:
            QMessageBox.warning(self, "Delete error", "No task is chosen")
        

class TodayTaskPage(QWidget):
    layout: QVBoxLayout
    
    def __init__(self, tasks=None, parent=None):
        super().__init__(parent)
        self.tasks = self.filterTasks(tasks)
        self.setWindowTitle("Today task")
        self.setupUI()
    
    def filterTasks(self, tasks):
        filter_tasks = []
        for idx, task in enumerate(tasks):
            if task['status'] == 'IN PROGRESS':
                filter_tasks.append({'idx': idx, 'data': task, 'reason': ''})
            elif task['do_date'] != '':
                task_date = datetime.strptime(task['do_date'], "%Y-%m-%d").date()
                current_date = datetime.now().date()
                if task['status'] == 'TO DO' and task_date <= current_date:
                    filter_tasks.append({'idx': idx, 'data': task, 'reason': ''})
                elif task_date == current_date:
                    filter_tasks.append({'idx': idx, 'data': task, 'reason': ''})
        return filter_tasks
    
    def setupUI(self):
        self.setMinimumSize(700, 300)
        table_headers = ["Category", "Task", "Status",
                         "Estimated hours", "Spent hours"]
        self.table = QTableWidget(len(self.tasks), len(table_headers))
        self.table.setHorizontalHeaderLabels(table_headers)
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: lightgray;
                color: black;
                font-weight: bold;
            }
        """)
        self.table.setWordWrap(True)
        # Fill some cells with data
        for row, task in enumerate(self.tasks):
            self.table.setItem(row, 0, QTableWidgetItem(task['data']['category']))
            self.table.setItem(row, 1, QTableWidgetItem(task['data']['task']))
            self.table.item(row, 1).setToolTip(task['data']['description'])
            for col in range(2):
                item = self.table.item(row, col)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Fill the status
            combobox = ComboxWithoutScrolling()
            combobox.addItems(CONFIG_DATA["status"])
            combobox.setCurrentText(task['data']['status'])
            combobox.currentTextChanged.connect(lambda text, idx=row: self.checkReasonNeeded(text, idx))
            self.table.setCellWidget(row, 2, combobox)
            
            # Fill the estimated hours
            self.table.setItem(row, 3, QTableWidgetItem(str(task['data']['estimated_hours'])))
            item = self.table.item(row, 3)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Fill the spent hours
            spent_hours = QLineEdit()
            spent_hours.setStyleSheet("border: none;")
            spent_hours.setText(str(task['data']['spent_hours']))
            self.table.setCellWidget(row, 4, spent_hours)
            double_validator = QDoubleValidator(0.0, 1000.0, 2, self)
            double_validator.setNotation(QDoubleValidator.Notation.StandardNotation) 
            spent_hours.setValidator(double_validator)
        
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        # Create a bold font
        font = QFont()
        font.setBold(True)

        # Apply the bold font to the horizontal header
        self.table.horizontalHeader().setFont(font)
        self.layout = QVBoxLayout()
        header_label = QLabel("<b>Today Tasks</b>")
        header_label.setStyleSheet("font-size: 18px")
        self.layout.addWidget(header_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.table)
        self.setupSaveButton()
        self.setLayout(self.layout)
        
    def setupSaveButton(self):
        self.save_btn = QPushButton("SAVE")
        self.save_btn.setStyleSheet(f"background-color: {BOSCHTURQUOISE_COLOR};color: white; font-weight: bold;")
        self.save_btn.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.save_btn.clicked.connect(self.saveTodayTask)
        # self.save_btn.setEnabled(True)
        # self.save_btn.setStyleSheet("""
        #     QPushButton:disabled {
        #         background-color: gray;
        #         color: white;
        #     }
        # """)
        self.layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def saveTodayTask(self):
        '''Save today tasks change to the database
        '''
        for idx, task in enumerate(self.tasks):
            task['data']['status'] = self.table.cellWidget(idx, 2).currentText()
            task['data']['spent_hours'] = self.table.cellWidget(idx, 4).text()
            if task['data']['status'] in REASON_STATUS:
                task['data']['reason'] = task['reason']
            print(f"Updating Task: {task['data']}")
            edit_task_item(CONFIG_DATA['database'], task['idx'], task['data'])
        self.table.clearSelection()
        self.triggerInfoMessage("Success", "Today task is updated succesfully!")
    
    def checkReasonNeeded(self, text, index):
        '''Check the reason field is necessary to added
        When the status of the task is changed to block or canceled,
        a reason must be provided.
        '''
        if text in REASON_STATUS:
            current_task = self.tasks[index]['data']
            dlg = ReasonInputDialog(self, data={'category': current_task['category'],
                                                'task':  current_task['task'],
                                                'status': f'<span style="color: red;">{current_task["status"]} -> {text}</span>'})
            # If the dialog is closed without the reason is provided
            # then revert the status back to its original state
            if dlg.exec() == QDialog.DialogCode.Rejected:
                combobox: QComboBox = self.table.cellWidget(index, 2)
                combobox.setCurrentText(current_task["status"])
            else:
                self.tasks[index]['reason'] = dlg.getReason()
    
    def triggerInfoMessage(self, title, text):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(text)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.show()
        QTimer.singleShot(DIALOG_WAIT_TIME, dialog.close)

class SettingPage(QWidget):
    layout: QVBoxLayout
    configuration_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task Tracking")
        self.setMinimumWidth(700)
        self.setFixedHeight(120)
        if os.path.exists(CONFIG_DATA['database']):
            self.path = os.path.abspath(CONFIG_DATA['database'])
        else:
            self.path = ''
        self.setupUI()
    
    def setupUI(self):
        self.layout = QVBoxLayout()
        heading_label = QLabel("<b>Setting</b>")
        heading_label.setStyleSheet("font-size: 16px;")
        config_box = QFormLayout()
        self.database_field = FieldBrowseFileBox(self.path, self)
        config_box.addRow("Database path", self.database_field)
        self.layout.addWidget(heading_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(config_box)
        self.setupSaveButton()
        self.setLayout(self.layout)
    
    def setupSaveButton(self):
        self.save_btn = QPushButton("SAVE")
        self.save_btn.setStyleSheet(f"background-color: {BOSCHPURPLE_COLOR};color: white; font-weight: bold;")
        self.save_btn.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.save_btn.clicked.connect(self.saveConfiguration)
        self.layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def saveConfiguration(self):
        CONFIG_DATA['database'] = self.database_field.getPath()
        save_environment()
        self.configuration_changed.emit()
        self.hide()
     
class TaskTracking(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        # Setup the window dimension
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        self.start_page = StartPage(self)
        self.setCentralWidget(self.start_page)
        self._move2center()
         
    def _move2center(self):
         # Get the screen's geometry
        screen_geometry = QApplication.primaryScreen().geometry()

        # Get the window's geometry
        window_geometry = self.centralWidget().geometry()

        # Calculate the position for the window to be centered
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2

        # Move the window to the calculated position
        self.move(x, y)

def load_environment():
    global CONFIG_DATA
    # If no data file is found use the constant in source file
    if not os.path.exists(TASK_DATA_PATH):
        return 0
    with open(TASK_DATA_PATH, 'r') as task_data_file:
        CONFIG_DATA = json.load(task_data_file)

def save_environment():
    global CONFIG_DATA
    with open(TASK_DATA_PATH, 'w') as task_data_file:
        json.dump(CONFIG_DATA, task_data_file)

if __name__ == "__main__":
    load_environment()
    app = QApplication()
    app.setWindowIcon(QIcon('./resources/app_icon.png'))
    main_window = TaskTracking()
    main_window.show()
    sys.exit(app.exec())