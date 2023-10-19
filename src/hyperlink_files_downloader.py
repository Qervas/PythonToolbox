'''
hyperlink_files_downloader.py

Description:
    A simple GUI program that allows a user to input a URL and download all links of a specified file type (default is .pdf).

Usage:
    1. Ensure you have either PyQt5 or PyQt6 installed, along with `requests` and `beautifulsoup4`.
    2. Run the program: `python pdf_downloader.py`
    3. Enter the target URL in the provided text box.
    4. Optionally, specify the desired file type (e.g., '.txt', '.jpg'). Default is '.pdf'.
    5. Click the "Download" button to start downloading the files.
    6. Download progress will be shown in the text area below the button.

Dependencies:
    - PyQt5 or PyQt6
    - requests
    - beautifulsoup4

To install dependencies:
    pip install pyqt5 requests beautifulsoup4
    or
    pip install pyqt6 requests beautifulsoup4
'''

import sys
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Import handling for PyQt5 or PyQt6
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTextEdit, QFileDialog, QLabel
    from PyQt6.QtCore import QThread, pyqtSignal
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTextEdit, QFileDialog, QLabel
    from PyQt5.QtCore import QThread, pyqtSignal
    PYQT_VERSION = 5


class FileDownloader(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, url, save_folder, file_extension):
        super().__init__()
        self.url = url
        self.save_folder = save_folder
        self.file_extension = file_extension

    def run(self):
        try:
            response = requests.get(self.url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith(f'.{self.file_extension}')]
            for link in links:
                filename = os.path.join(self.save_folder, os.path.basename(link))
                with open(filename, 'wb') as f:
                    f.write(requests.get(urljoin(self.url, link)).content)
                self.update_signal.emit(f"Downloaded: {filename}")
        except Exception as e:
            self.update_signal.emit(str(e))


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('File Downloader')
        self.setGeometry(10, 10, 400, 280)

        layout = QVBoxLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter URL...")
        layout.addWidget(self.url_input)

        self.extension_input = QLineEdit(self)
        self.extension_input.setPlaceholderText("Enter file extension (default: pdf)...")
        layout.addWidget(self.extension_input)

        self.save_button = QPushButton("Choose Save Directory", self)
        self.save_button.clicked.connect(self.choose_save_directory)
        layout.addWidget(self.save_button)

        self.download_button = QPushButton("Download Files", self)
        self.download_button.clicked.connect(self.download_files)
        layout.addWidget(self.download_button)

        self.output = QTextEdit(self)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def choose_save_directory(self):
        self.save_folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if self.save_folder:
            self.save_button.setText(self.save_folder)

    def download_files(self):
        self.output.clear()
        url = self.url_input.text()
        file_extension = self.extension_input.text() or 'pdf'
        if not hasattr(self, 'save_folder'):
            self.output.setText("Please choose a save directory first.")
            return

        self.downloader = FileDownloader(url, self.save_folder, file_extension)
        self.downloader.update_signal.connect(self.update_output)
        self.downloader.start()

    def update_output(self, message: str):
        self.output.append(message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())
