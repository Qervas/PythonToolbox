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

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox, QWidget, QTimeEdit, QFileDialog, QSizePolicy
from PyQt5.QtCore import QTimer, QTime, QUrl, Qt, QFile, QIODevice
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont


import tempfile
import alarm_sound

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
		self.stop_button = QPushButton('Stop', self)
		self.stop_button.clicked.connect(self.stop_sessions)

		self.current_time_label = QLabel('00:00:00', self)
  
		  # Add button to select alarm sound
		self.select_alarm_button = QPushButton('Select Alarm Sound', self)
		self.select_alarm_button.clicked.connect(self.select_alarm_sound)

		self.study_time_label = QLabel('Study Time:')
		self.relax_time_label = QLabel('Relax Time:')

		# Layouts
		input_layout = QHBoxLayout()
		input_layout.addWidget(self.study_time_label)
		input_layout.addWidget(self.study_time_input)
		input_layout.addWidget(self.relax_time_label)
		input_layout.addWidget(self.relax_time_input)
		input_layout.addWidget(self.add_session_button)
		input_layout.addWidget(self.clear_sessions_button)

		main_layout = QVBoxLayout()
		main_layout.addLayout(input_layout)
		main_layout.addWidget(self.session_list)
		main_layout.addWidget(self.start_button)
		main_layout.addWidget(self.stop_button)
		main_layout.addWidget(self.current_time_label)
		main_layout.addWidget(self.select_alarm_button)
		  # Add the stop button to the main layout
		# main_layout = self.centralWidget().layout()

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
		self.temp_alarm_file = self.extract_resource_to_temp(":/alarm.wav")
		self.media_player = QMediaPlayer(self)
		self.alarm_sound_path = self.temp_alarm_file
		self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.alarm_sound_path)))
  
		  # Adjust size policies for dynamic resizing
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		self.study_time_input.setSizePolicy(size_policy)
		self.relax_time_input.setSizePolicy(size_policy)
		self.add_session_button.setSizePolicy(size_policy)
		self.clear_sessions_button.setSizePolicy(size_policy)
		self.session_list.setSizePolicy(size_policy)
		self.start_button.setSizePolicy(size_policy)	
		self.stop_button.setSizePolicy(size_policy)
		self.current_time_label.setSizePolicy(size_policy)
		self.select_alarm_button.setSizePolicy(size_policy)
  
	def extract_resource_to_temp(self, resource_path):
		# Create a QFile object for the resource
		file = QFile(resource_path)
		
		# Open the resource file for reading
		if not file.open(QIODevice.ReadOnly):
			raise Exception(f"Failed to open resource: {resource_path}")
		
		# Read the resource into a QByteArray
		byte_array = file.readAll()
		
		# Close the resource file
		file.close()
		
		# Extract the resource to a temporary file and return its path
		temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
		temp_file.write(byte_array.data())
		return temp_file.name
  
	def resizeEvent(self, event):
		super().resizeEvent(event)
		# Adjust font sizes on window resize
		self.adjust_font_sizes()
  
	def adjust_font_sizes(self):
		# Determine base font size based on the window's height
		base_font_size = self.height() * 0.025

		# Create a QFont object with the calculated font size
		dynamic_font = QFont()
		dynamic_font.setPointSize(int(base_font_size))

		# Adjust font for current_time_label and other QLabel widgets
		for label in [self.current_time_label]:
			label.setFont(dynamic_font)

		# Adjust font for QTimeEdit widgets
		for widget in [self.study_time_input, self.relax_time_input]:
			widget.setFont(dynamic_font)

		# Adjust font for buttons
		for btn in [self.add_session_button, self.clear_sessions_button, self.start_button, self.stop_button, self.select_alarm_button]:
			btn.setFont(dynamic_font)

		# Adjust font for QListWidget items
		for index in range(self.session_list.count()):
			item = self.session_list.item(index)
			item.setFont(dynamic_font)
	
		# Adjust font for study_time_label and relax_time_label
		for label in [self.study_time_label, self.relax_time_label]:
			label.setFont(QFont(self.font().family(), int(self.height() * 0.025)))


	def add_session(self):
		study_time = self.study_time_input.time().toString()
		relax_time = self.relax_time_input.time().toString()
		self.sessions.append((study_time, relax_time))
		self.session_list.addItem(f"Study: {study_time} | Relax: {relax_time}")
  
	def clear_sessions(self):
		self.sessions.clear()
		self.session_list.clear()
		self.current_session_index = -1
		self.is_study_time = True
		self.stop_sessions()

	def start_sessions(self):
		if not self.sessions:
			QMessageBox.warning(self, 'Warning', 'Please add at least one session.')
			return
		self.current_session_index = 0
		self.is_study_time = True  # Ensure we start with study time
		self.start_next_session(play_sound=False)

	def start_next_session(self, play_sound=True):
		if play_sound:  # Only play sound if the flag is set
			self.media_player.play()
		if self.is_study_time:
			self.current_time = QTime.fromString(self.sessions[self.current_session_index][0])
			self.show_non_blocking_message('Start Studying', 'Time to study!')
		else:
			self.current_time = QTime.fromString(self.sessions[self.current_session_index][1])
			self.show_non_blocking_message('Relax', 'Time to relax!')

		self.timer.start(1000)

	def show_non_blocking_message(self, title, message):
		msg = QMessageBox(self)
		msg.setWindowTitle(title)
		msg.setText(message)
		msg.setFont(QFont(self.font().family(), int(self.height() * 0.025)))  # Adjust font size dynamically
		msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
		msg.show()

	def update_time(self):
		self.current_time = self.current_time.addSecs(-1)
		self.current_time_label.setText(self.current_time.toString())

		if self.current_time == QTime(0, 0):
			self.timer.stop()
			self.is_study_time = not self.is_study_time
			if self.is_study_time:  # If it's the end of relax time
				self.current_session_index += 1
			if self.current_session_index >= len(self.sessions):
				self.media_player.play()
				self.show_non_blocking_message('Done', 'All sessions completed!')
				return
			self.start_next_session()

	def stop_sessions(self):
		"""Stop the timer and reset the sessions."""
		self.timer.stop()
		self.current_time_label.setText('00:00:00')
		self.current_session_index = -1
		self.is_study_time = True
		QMessageBox.information(self, 'Stopped', 'Sessions have been stopped.')

   
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

