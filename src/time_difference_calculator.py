"""
Time Difference Calculator - User Manual

Description:
-------------
The Time Difference Calculator is a PyQt5-based application designed to calculate the time difference 
between two given points in time. The application provides an intuitive GUI, allowing users to easily 
select date-times, set them to the current time, and view the calculated difference in terms of years, 
months, days, hours, minutes, and seconds.

Usage:
------
1. Launch the application to view the main window.

2. Date-Time Selection:
   - The application presents two date-time input fields.
   - Use these fields to select the desired date-times for comparison.
   - Alternatively, use the checkboxes labeled 'Now' to set the respective date-time to the current time. 
     When 'Now' is selected for a date-time, it will update every second.

3. Date Format:
   - Below the date-time input fields, there's an input field labeled 'Date Format'.
   - The default format is set as "yyyy-MM-dd HH:mm:ss".
   - You can modify this format as needed. For example, to only display the date, you could use "yyyy-MM-dd".
   - After changing the format in the input field, click the 'Apply Format' button to update the date-time displays.

4. Calculate Difference:
   - Press the "Calculate Difference" button located below the date-time input fields.
   - The application will compute and display the difference between the two times in terms of years, 
     months, days, hours, minutes, and seconds.

Note:
-----
- The application uses a simple heuristic to determine months and years from days (30 days to a month, 365 days to a year). 
  This means the calculated months and years might not always match calendar months and years, but it provides a general idea.

"""

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QWidget, QDateTimeEdit, QCheckBox)
from PyQt5.QtCore import QTimer, QDateTime

class TimeDifferenceCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Time Difference Calculator')

        # Create widgets
        self.datetime1_input = QDateTimeEdit(self)
        self.datetime1_input.setDateTime(QDateTime.currentDateTime())
        self.datetime1_now_checkbox = QCheckBox("Now", self)
        self.datetime1_now_checkbox.toggled.connect(self.toggle_now_datetime1)

        self.datetime2_input = QDateTimeEdit(self)
        self.datetime2_input.setDateTime(QDateTime.currentDateTime())
        self.datetime2_now_checkbox = QCheckBox("Now", self)
        self.datetime2_now_checkbox.toggled.connect(self.toggle_now_datetime2)

        self.calculate_button = QPushButton('Calculate Difference', self)
        self.calculate_button.clicked.connect(self.calculate_difference)

        self.result_label = QLabel('', self)

        # Layouts
        datetime1_layout = QHBoxLayout()
        datetime1_layout.addWidget(QLabel('Date-Time 1:'))
        datetime1_layout.addWidget(self.datetime1_input)
        datetime1_layout.addWidget(self.datetime1_now_checkbox)

        datetime2_layout = QHBoxLayout()
        datetime2_layout.addWidget(QLabel('Date-Time 2:'))
        datetime2_layout.addWidget(self.datetime2_input)
        datetime2_layout.addWidget(self.datetime2_now_checkbox)

        main_layout = QVBoxLayout()
        main_layout.addLayout(datetime1_layout)
        main_layout.addLayout(datetime2_layout)
        main_layout.addWidget(self.calculate_button)
        main_layout.addWidget(self.result_label)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Timer to update every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_now)
        self.timer.start(1000)
        
                # Add widget for date format selection
        self.date_format_input = QLineEdit(self)
        self.date_format_input.setText("yyyy-MM-dd HH:mm:ss")
        self.apply_format_button = QPushButton('Apply Format', self)
        self.apply_format_button.clicked.connect(self.apply_date_format)

        # Insert the new widgets into the main layout
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('Date Format:'))
        format_layout.addWidget(self.date_format_input)
        format_layout.addWidget(self.apply_format_button)
        
        main_layout = self.centralWidget().layout()
        main_layout.insertLayout(2, format_layout)

    def toggle_now_datetime1(self, checked):
        self.datetime1_input.setDisabled(checked)
        if checked:
            self.datetime1_input.setDateTime(QDateTime.currentDateTime())

    def toggle_now_datetime2(self, checked):
        self.datetime2_input.setDisabled(checked)
        if checked:
            self.datetime2_input.setDateTime(QDateTime.currentDateTime())

    def update_now(self):
        # Update the input fields to "now" if the corresponding checkbox is checked
        if self.datetime1_now_checkbox.isChecked():
            self.datetime1_input.setDateTime(QDateTime.currentDateTime())
        if self.datetime2_now_checkbox.isChecked():
            self.datetime2_input.setDateTime(QDateTime.currentDateTime())

        # Recalculate difference
        self.calculate_difference()

    def calculate_difference(self):
        dt1 = self.datetime1_input.dateTime().toPyDateTime()
        dt2 = self.datetime2_input.dateTime().toPyDateTime()

        if dt1 > dt2:
            dt1, dt2 = dt2, dt1

        delta = dt2 - dt1

        years, days = divmod(delta.days, 365)
        months, days = divmod(days, 30)
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        result_str = f"Years: {years}, Months: {months}, Days: {days}, Hours: {hours}, Minutes: {minutes}, Seconds: {seconds}"
        self.result_label.setText(result_str)
        
    def apply_date_format(self):
        date_format = self.date_format_input.text()
        self.datetime1_input.setDisplayFormat(date_format)
        self.datetime2_input.setDisplayFormat(date_format)
        # Update the current date-times to reflect the new format
        self.datetime1_input.setDateTime(self.datetime1_input.dateTime())
        self.datetime2_input.setDateTime(self.datetime2_input.dateTime())

if __name__ == '__main__':
    app = QApplication([])
    window = TimeDifferenceCalculator()
    window.show()
    app.exec_()

