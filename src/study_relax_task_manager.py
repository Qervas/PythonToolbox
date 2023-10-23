'''
Study & Relax Task Manager - User Manual

Description:
-------------
This application provides a graphical user interface to help users manage study and relaxation sessions. 
It allows users to set durations for study and relaxation, add these durations as sessions, and then start 
a countdown timer for these sessions. When transitioning between study and relaxation times, an alarm sound 
will play to notify the user.

Usage:
-------------
1. **Launch the Program**:
   - Upon launching, you'll see input fields for setting study and relaxation times, buttons for adding and
   clearing sessions, a list displaying the sessions, a button to start the timer, and a label displaying the 
   current countdown time.

2. **Setting Study and Relaxation Times**:
   - Use the time input fields labeled 'Study Time' and 'Relax Time' to set your desired durations. You can either
   type in the times or use the up and down arrows to adjust them.

3. **Adding Sessions**:
   - Once you've set the desired study and relaxation times, click the 'Add Session' button. This will add the times
   as a session and display them in the list below.

4. **Clearing Sessions**:
   - If you wish to clear all the sessions you've added, click the 'Clear Sessions' button.

5. **Selecting an Alarm Sound**:
   - Click the 'Select Alarm Sound' button to open a file dialog.
   - Navigate to and select the audio file (e.g., .mp3 or .wav) you wish to use as the alarm sound. This sound will 
   play when transitioning between study and relaxation times.

6. **Starting the Countdown Timer**:
   - Once you've added your sessions, click the 'Start' button to begin the countdown timer.
   - The timer will start with the study time of the first session and count down to zero. When the study time ends, 
   the relaxation time will begin counting down.
   - The current countdown time is displayed below the 'Start' button.
   - When transitioning between study and relaxation times, the selected alarm sound will play, and a notification 
   will appear to inform you.

7. **End of Sessions**:
   - Once all sessions are complete, a notification will inform you that all sessions have finished.

Dependencies:
-------------
Ensure you have the following Python packages installed:
- PyQt5: For the graphical user interface.
- PyQt5.QtMultimedia: For playing the alarm sound.
'''

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox, QWidget, QTimeEdit, QFileDialog
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl


class TaskManagerApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.init_ui()

	def init_ui(self):
		self.setWindowTitle('Study & Relax Task Manager')

		# Create widgets
		self.study_time_input = QTimeEdit(self)
		self.study_time_input.setDisplayFormat("HH:mm:ss")
		self.relax_time_input = QTimeEdit(self)
		self.relax_time_input.setDisplayFormat("HH:mm:ss")

		self.add_session_button = QPushButton('Add Session', self)
		self.add_session_button.clicked.connect(self.add_session)

		self.clear_sessions_button = QPushButton('Clear Sessions', self)
		self.clear_sessions_button.clicked.connect(self.clear_sessions)

		self.session_list = QListWidget(self)

		self.start_button = QPushButton('Start', self)
		self.start_button.clicked.connect(self.start_sessions)

		self.current_time_label = QLabel('00:00:00', self)
  
		  # Add button to select alarm sound
		self.select_alarm_button = QPushButton('Select Alarm Sound', self)
		self.select_alarm_button.clicked.connect(self.select_alarm_sound)

		# Layouts
		input_layout = QHBoxLayout()
		input_layout.addWidget(QLabel('Study Time:'))
		input_layout.addWidget(self.study_time_input)
		input_layout.addWidget(QLabel('Relax Time:'))
		input_layout.addWidget(self.relax_time_input)
		input_layout.addWidget(self.add_session_button)
		input_layout.addWidget(self.clear_sessions_button)

		main_layout = QVBoxLayout()
		main_layout.addLayout(input_layout)
		main_layout.addWidget(self.session_list)
		main_layout.addWidget(self.start_button)
		main_layout.addWidget(self.current_time_label)
		main_layout.addWidget(self.select_alarm_button)

		central_widget = QWidget()
		central_widget.setLayout(main_layout)
		self.setCentralWidget(central_widget)

		# Attributes for handling sessions
		self.sessions = []
		self.current_session_index = -1
		self.is_study_time = True
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_time)

		# Set up media player for alarm sound
		self.alarm_sound_path = "alarm.mp3"
		self.media_player = QMediaPlayer(self)
		self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.alarm_sound_path)))

	def add_session(self):
		study_time = self.study_time_input.time().toString()
		relax_time = self.relax_time_input.time().toString()
		self.sessions.append((study_time, relax_time))
		self.session_list.addItem(f"Study: {study_time} | Relax: {relax_time}")
  
	def clear_sessions(self):
		self.sessions.clear()
		self.session_list.clear()

	def start_sessions(self):
		if not self.sessions:
			QMessageBox.warning(self, 'Warning', 'Please add at least one session.')
			return
		self.current_session_index = 0
		self.is_study_time = True  # Ensure we start with study time
		self.start_next_session()

	def start_next_session(self):
		if self.current_session_index >= len(self.sessions):
			QMessageBox.information(self, 'Done', 'All sessions completed!')
			return

		study_time, relax_time = self.sessions[self.current_session_index]
		if self.is_study_time:
			self.current_time = QTime.fromString(study_time)
			QMessageBox.information(self, 'Start Studying', 'Time to study!')
		else:
			self.current_time = QTime.fromString(relax_time)
			QMessageBox.information(self, 'Relax', 'Time to relax!')

		self.media_player.play()
		self.timer.start(1000)
		self.is_study_time = not self.is_study_time

	def update_time(self):
		self.current_time = self.current_time.addSecs(-1)
		self.current_time_label.setText(self.current_time.toString())

		if self.current_time == QTime(0, 0):
			self.timer.stop()
			if not self.is_study_time:
				self.current_session_index += 1
			self.start_next_session()
	def select_alarm_sound(self):
		options = QFileDialog.Options()
		file_name, _ = QFileDialog.getOpenFileName(self, "Select Alarm Sound", "", "Audio Files (*.mp3 *.wav);;All Files (*)", options=options)
		if file_name:
			self.alarm_sound_path = file_name
			self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.alarm_sound_path)))

if __name__ == '__main__':
	app = QApplication([])
	window = TaskManagerApp()
	window.show()
	app.exec_()

