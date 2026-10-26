import os
import sys
import re
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QToolBar, QAction, QFileDialog, QSpacerItem
) 
from PyQt5.QtGui import QIntValidator, QFont, QPainter, QBrush, QColor, QPainterPath, QLinearGradient
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
import csv

# Custom widget to draw a stylish wave divider with glow effect
class WaveDivider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(100)  # Wider for a more prominent wave

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # Get widget dimensions
        width = self.width()
        height = self.height()

        # Create a wave path with multiple curves
        path = QPainterPath()
        path.moveTo(0, 0)  # Start at top-left

        # Wave parameters
        wave_height = height / 4  # Smaller waves for elegance
        for i in range(4):  # Four waves for a richer pattern
            start_y = i * wave_height
            mid_y = start_y + wave_height / 2
            end_y = (i + 1) * wave_height if i < 3 else height

            path.cubicTo(
                width * 0.25, start_y + wave_height * 0.3,  # First control point
                width * 0.75, start_y + wave_height * 0.7,  # Second control point
                width, mid_y  # Midpoint of wave
            )
            if i < 3:
                path.cubicTo(
                    width * 0.75, mid_y + wave_height * 0.3,  # First control point
                    width * 0.25, mid_y + wave_height * 0.7,  # Second control point
                    0, end_y  # End of wave segment
                )

        path.lineTo(width, 0)
        path.lineTo(0, 0)

        # Gradient for the divider
        gradient = QLinearGradient(0, 0, width, 0)
        gradient.setColorAt(0, QColor("#4CB8C4"))
        gradient.setColorAt(0.5, QColor("#3A8A9E"))
        gradient.setColorAt(1, QColor("#2D6A7F"))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)

        # Add a subtle glow effect
        painter.setBrush(QBrush(QColor("#4CB8C4").lighter(150)))
        for offset in [-5, 5]:
            painter.drawPath(path.translated(offset, 0))

# Main Window for Demographics Form
class DemographicsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demographics Form")

        # Set window size
        screen = QApplication.primaryScreen()
        self.resize(1280, 720)

        # Set modern base styles
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F5F7FA, stop:1 #E8ECEF);
            }
            QLabel {
                color: #2D2D2D;
                font-family: 'Helvetica', Arial, sans-serif;
            }
        """)

        # Create toolbar with professional styling
        self.create_toolbar()

        # Set up central widget and main vertical layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

        # Horizontal layout for the entire window with split background
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Left Side: White Section with Inputs
        self.left_container = QWidget()
        self.left_container.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        """)
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(120, 60, 40, 60)
        self.left_layout.setSpacing(25)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Welcome Title
        self.title_label = QLabel("Welcome To AIKAT")
        self.title_label.setStyleSheet("font-size: 36px; font-weight: bold; margin-bottom: 40px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.left_layout.addWidget(self.title_label)

        # Sub-title
        self.subtitle_label = QLabel("Please enter your details")
        self.subtitle_label.setStyleSheet("font-size: 18px; color: #555555; margin-bottom: 30px;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.left_layout.addWidget(self.subtitle_label)

        # Uniform input box styles with hover effect
        input_style = """
            padding: 12px;
            font-size: 16px;
            font-family: 'Helvetica', Arial, sans-serif;
            border: 1px solid #CCCCCC;
            border-radius: 10px;
            background-color: #F9F9F9;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        """
        input_hover_style = """
            border: 1px solid #4CB8C4;
            background-color: #F0F5F7;
        """
        input_box_width = 340

        # Name Row
        self.name_row = QHBoxLayout()
        self.name_label = QLabel("Name:")
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-right: 20px;")
        self.name_label.setFixedWidth(180)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")
        self.name_input.setStyleSheet(input_style)
        self.name_input.setFixedWidth(input_box_width)
        self.name_input.setProperty("hoverStyle", input_hover_style)
        self.name_input.enterEvent = lambda e: self.name_input.setStyleSheet(input_style + input_hover_style)
        self.name_input.leaveEvent = lambda e: self.name_input.setStyleSheet(input_style)
        self.name_row.addWidget(self.name_label)
        self.name_row.addWidget(self.name_input)
        self.name_row.addStretch()
        self.left_layout.addLayout(self.name_row)

        # Age Row
        self.age_row = QHBoxLayout()
        self.age_label = QLabel("Age:")
        self.age_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-right: 20px;")
        self.age_label.setFixedWidth(180)
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Enter your age")
        self.age_input.setValidator(QIntValidator(0, 120))
        self.age_input.setStyleSheet(input_style)
        self.age_input.setFixedWidth(input_box_width)
        self.age_input.setProperty("hoverStyle", input_hover_style)
        self.age_input.enterEvent = lambda e: self.age_input.setStyleSheet(input_style + input_hover_style)
        self.age_input.leaveEvent = lambda e: self.age_input.setStyleSheet(input_style)
        self.age_row.addWidget(self.age_label)
        self.age_row.addWidget(self.age_input)
        self.age_row.addStretch()
        self.left_layout.addLayout(self.age_row)

        # Gender Row
        self.gender_row = QHBoxLayout()
        self.gender_label = QLabel("Gender:")
        self.gender_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-right: 20px;")
        self.gender_label.setFixedWidth(180)
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Select Gender", "Male", "Female", "Other"])
        self.gender_input.setStyleSheet(input_style)
        self.gender_input.setFixedWidth(input_box_width)
        self.gender_input.setProperty("hoverStyle", input_hover_style)
        self.gender_input.enterEvent = lambda e: self.gender_input.setStyleSheet(input_style + input_hover_style)
        self.gender_input.leaveEvent = lambda e: self.gender_input.setStyleSheet(input_style)
        self.gender_row.addWidget(self.gender_label)
        self.gender_row.addWidget(self.gender_input)
        self.gender_row.addStretch()
        self.left_layout.addLayout(self.gender_row)

        # Dominant Hand Row
        self.hand_row = QHBoxLayout()
        self.hand_label = QLabel("Dominant Hand:")
        self.hand_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-right: 20px;")
        self.hand_label.setFixedWidth(180)
        self.hand_input = QComboBox()
        self.hand_input.addItems(["Select Hand", "Right", "Left", "Ambidextrous"])
        self.hand_input.setStyleSheet(input_style)
        self.hand_input.setFixedWidth(input_box_width)
        self.hand_input.setProperty("hoverStyle", input_hover_style)
        self.hand_input.enterEvent = lambda e: self.hand_input.setStyleSheet(input_style + input_hover_style)
        self.hand_input.leaveEvent = lambda e: self.hand_input.setStyleSheet(input_style)
        self.hand_row.addWidget(self.hand_label)
        self.hand_row.addWidget(self.hand_input)
        self.hand_row.addStretch()
        self.left_layout.addLayout(self.hand_row)

        # Error Message
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #D32F2F; font-size: 16px; font-family: 'Helvetica', Arial, sans-serif;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.left_layout.addWidget(self.message_label)

        # Add spacer to center vertically
        self.left_layout.addStretch()

        # Set stretch factor for left side
        self.main_layout.addWidget(self.left_container, stretch=1)

        # Add the stylish wave divider
        self.divider = WaveDivider()
        self.main_layout.addWidget(self.divider)

        # Right Side: Submit Button
        self.right_container = QWidget()
        self.right_container.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CB8C4, stop:1 #2D6A7F);
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        """)
        self.right_layout = QHBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)

        # Submit Button Container
        self.submit_container = QWidget()
        self.submit_layout = QVBoxLayout(self.submit_container)
        self.submit_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.submit_layout.setContentsMargins(0, 0, 50, 0)

        # Vertical spacer to center the button
        self.submit_layout.addStretch()

        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFFFF, stop:1 #F0F0F0);
                color: #2D2D2D;
                font-size: 20px;
                font-weight: bold;
                font-family: 'Helvetica', Arial, sans-serif;
                padding: 15px 30px;
                border-radius: 12px;
                border: 1px solid #CCCCCC;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E0E0E0, stop:1 #D0D0D0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C0C0C0, stop:1 #B0B0B0);
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
        """)
        self.submit_button.clicked.connect(self.open_new_page)
        # Add animation for button hover
        self.submit_button_hover = QPropertyAnimation(self.submit_button, b"geometry")
        self.submit_button_hover.setEasingCurve(QEasingCurve.OutQuad)
        self.submit_button.enterEvent = lambda e: self.animate_button(True)
        self.submit_button.leaveEvent = lambda e: self.animate_button(False)
        self.submit_layout.addWidget(self.submit_button)

        # Vertical spacer to center the button
        self.submit_layout.addStretch()

        self.right_layout.addWidget(self.submit_container)

        # Set stretch factor for right side
        self.main_layout.addWidget(self.right_container, stretch=1)

        # Add the main layout to the central layout
        self.central_layout.addLayout(self.main_layout)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E8ECEF, stop:1 #D3D3D3);
                border: none;
                padding: 5px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            }
            QAction {
                color: #2D2D2D;
                font-size: 14px;
                font-family: 'Helvetica', Arial, sans-serif;
                padding: 5px 12px;
                border-radius: 5px;
            }
            QAction:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CB8C4, stop:1 #3A8A9E);
                color: #FFFFFF;
            }
        """)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)

        compare_action = QAction("Compare", self)
        compare_action.triggered.connect(self.compare_users)
        toolbar.addAction(compare_action)

        increase_font_action = QAction("Increase Font Size", self)
        increase_font_action.triggered.connect(self.increase_font_size)
        toolbar.addAction(increase_font_action)

        decrease_font_action = QAction("Decrease Font Size", self)
        decrease_font_action.triggered.connect(self.decrease_font_size)
        toolbar.addAction(decrease_font_action)

    def animate_button(self, hover):
        if hover:
            self.submit_button_hover.setStartValue(self.submit_button.geometry())
            self.submit_button_hover.setEndValue(self.submit_button.geometry().adjusted(-5, -5, 5, 5))
            self.submit_button_hover.setDuration(200)
            self.submit_button_hover.start()
        else:
            self.submit_button_hover.setStartValue(self.submit_button.geometry())
            self.submit_button_hover.setEndValue(self.submit_button.geometry().adjusted(5, 5, -5, -5))
            self.submit_button_hover.setDuration(200)
            self.submit_button_hover.start()

    def open_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt)", options=options)
        if file_name:
            print(f"Opened file: {file_name}")

    def compare_users(self):
        print("Comparing users...")

    def increase_font_size(self):
        current_font = self.title_label.font()
        current_font.setPointSize(current_font.pointSize() + 1)
        self.title_label.setFont(current_font)

    def decrease_font_size(self):
        current_font = self.title_label.font()
        current_font.setPointSize(max(1, current_font.pointSize() - 1))
        self.title_label.setFont(current_font)

    def open_new_page(self):
        name = self.name_input.text().strip()
        age = self.age_input.text().strip()
        gender = self.gender_input.currentText()
        hand = self.hand_input.currentText()

        if not name or not age or gender == "Select Gender" or hand == "Select Hand":
            self.show_message("Please fill out the form correctly.")
            return

        if not re.match(r"^[a-zA-Z\s]+$", name):
            self.show_message("Name can only contain letters and spaces.")
            return

        sanitized_name = re.sub(r'[<>:"/\\|?*]', '', name)
        participant_folder = os.path.join(os.getcwd(), sanitized_name)
        try:
            os.makedirs(participant_folder, exist_ok=True)
            subfolders = ["Tracing", "Tracking", "Aiming"]
            for subfolder in subfolders:
                os.makedirs(os.path.join(participant_folder, subfolder), exist_ok=True)
        except Exception as e:
            self.show_message(f"Error creating folder: {e}")
            return

        csv_file = 'demographics.csv'
        file_exists = os.path.isfile(csv_file)
        try:
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Name", "Gender", "Age", "Dominant Hand"])
                writer.writerow([name, gender, age, hand])
        except Exception as e:
            self.show_message(f"Error saving to CSV: {e}")
            return

        self.new_page = TaskPage(name, age, gender, hand)
        self.new_page.show()
        self.close()

    def show_message(self, message):
        self.message_label.setText(message)

# Task Page with Buttons
class TaskPage(QMainWindow):
    task_completed = pyqtSignal()

    def __init__(self, name, age, gender, hand):
        super().__init__()
        self.setWindowTitle("Task Selection")
        self.resize(700, 400)

        self.demographics = {
            'Name': name,
            'Age': age,
            'Gender': gender,
            'Dominant Hand': hand
        }

        # Set modern background
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F5F7FA, stop:1 #E8ECEF);
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        self.create_toolbar()

        # Title
        self.title_label = QLabel("Welcome to the Task Page")
        self.title_label.setStyleSheet("font-size: 26px; font-weight: bold; font-family: 'Helvetica', Arial, sans-serif; color: #2D2D2D;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)

        # User Info
        self.label = QLabel(f"User Info: {self.demographics}")
        self.label.setStyleSheet("font-size: 16px; font-family: 'Helvetica', Arial, sans-serif; color: #555555;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        # Button style
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CB8C4, stop:1 #2D6A7F);
                color: #FFFFFF;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Helvetica', Arial, sans-serif;
                padding: 14px 28px;
                border-radius: 12px;
                border: none;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3A8A9E, stop:1 #1F4A5E);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2D6A7F, stop:1 #1A3A4A);
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
        """

        # Task Button
        self.button1 = QPushButton("Start Tasks")
        self.button1.setStyleSheet(button_style)
        self.button1.clicked.connect(self.run_button1)
        self.layout.addWidget(self.button1, alignment=Qt.AlignmentFlag.AlignCenter)

        # Back Button
        self.back_button = QPushButton("Back to Demographics Form")
        self.back_button.setStyleSheet(button_style)
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add vertical spacer
        self.layout.addStretch()

        self.central_widget.setLayout(self.layout)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E8ECEF, stop:1 #D3D3D3);
                border: none;
                padding: 5px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            }
            QAction {
                color: #2D2D2D;
                font-size: 14px;
                font-family: 'Helvetica', Arial, sans-serif;
                padding: 5px 12px;
                border-radius: 5px;
            }
            QAction:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CB8C4, stop:1 #3A8A9E);
                color: #FFFFFF;
            }
        """)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)

        compare_action = QAction("Compare", self)
        compare_action.triggered.connect(self.compare_users)
        toolbar.addAction(compare_action)

        increase_font_action = QAction("Increase Font Size", self)
        increase_font_action.triggered.connect(self.increase_font_size)
        toolbar.addAction(increase_font_action)

        decrease_font_action = QAction("Decrease Font Size", self)
        decrease_font_action.triggered.connect(self.decrease_font_size)
        toolbar.addAction(decrease_font_action)

    def open_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt)", options=options)
        if file_name:
            print(f"Opened file: {file_name}")

    def compare_users(self):
        print("Comparing users...")

    def increase_font_size(self):
        current_font = self.title_label.font()
        current_font.setPointSize(current_font.pointSize() + 1)
        self.title_label.setFont(current_font)

    def decrease_font_size(self):
        current_font = self.title_label.font()
        current_font.setPointSize(max(1, current_font.pointSize() - 1))
        self.title_label.setFont(current_font)

    def run_button1(self):
        self.hide()
        self.task_thread = TaskThread(self.demographics, button_number=1)
        self.task_thread.task_completed.connect(self.show_task_selection)
        self.task_thread.start()

    def show_task_selection(self):
        self.show()

    def go_back(self):
        self.demographics_page = DemographicsApp()
        self.demographics_page.show()
        self.close()

class TaskThread(QThread):
    task_completed = pyqtSignal()

    def __init__(self, demographics, button_number):
        super().__init__()
        self.demographics = demographics
        self.button_number = button_number

    def run(self):
        if self.button_number == 1:
            subprocess.run([sys.executable, 'InitialPygame.py'])
        self.task_completed.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemographicsApp()
    window.show()
    sys.exit(app.exec_())