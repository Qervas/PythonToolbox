import PyPDF2
import requests

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit, QVBoxLayout, QWidget
    from PyQt6.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit, QVBoxLayout, QWidget
    from PyQt5.QtCore import Qt


class PDFDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create widgets
        self.load_button = QPushButton('Load PDF', self)
        self.load_button.clicked.connect(self.load_pdf)

        self.choose_folder_button = QPushButton('Choose Download Folder', self)
        self.choose_folder_button.clicked.connect(self.choose_folder)
        self.download_folder = ''  # Initialize with an empty string

        self.start_download_button = QPushButton('Start Download', self)
        self.start_download_button.clicked.connect(self.start_download)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        
        self.links=[]

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addWidget(self.choose_folder_button)
        layout.addWidget(self.start_download_button)
        layout.addWidget(self.text_edit)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)
        self.setWindowTitle('PDF Downloader')
        self.resize(400, 300)

    def load_pdf(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_name:
            self.links = extract_links_from_pdf(file_name)
            self.text_edit.setPlainText('\n'.join(self.links))
        else:
            self.text_edit.append("\nFailed to load PDF. Please try again.")
    def choose_folder(self):
        self.download_folder = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if self.download_folder:
            current_text = self.text_edit.toPlainText()
            self.text_edit.setPlainText(current_text + f"\nSelected download folder: {self.download_folder}")


    def start_download(self):
        if not self.download_folder:
            self.text_edit.append("\nPlease choose a download folder first!")
            return
        if not hasattr(self, 'links') or not self.links:
            self.text_edit.append("\nPlease load a PDF file first!")
            return
        download_files_from_links(self.links, self.download_folder)
        self.text_edit.append("\nDownload completed!")


def extract_links_from_pdf(pdf_path):
    links = []
    
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            if page.get('/Annots'):
                annotations = page['/Annots']
                for annotation in annotations:
                    uri = annotation.get_object().get("/A").get("/URI")
                    if uri:
                        links.append(uri)
    return links

def download_files_from_links(links, download_folder='.'):
    for link in links:
        response = requests.get(link)
        filename = link.split('/')[-1]
        with open(f"{download_folder}/{filename}", 'wb') as f:
            f.write(response.content)

if __name__ == '__main__':
    app = QApplication([])
    window = PDFDownloaderApp()
    window.show()
    app.exec()
