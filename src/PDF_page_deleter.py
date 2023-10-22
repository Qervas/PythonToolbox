'''
PDF Page Deleter User Manual

Description:
-------------
This program provides a graphical user interface to load a PDF file, preview its pages,
and delete specific pages from the PDF. Once the desired pages are deleted, the changes
can be saved to create a modified PDF file.

Usage:
-------------
1. Launch the program. The main window will display control buttons on the left and a 
	PDF preview area on the right.

2. Click the "Load PDF" button to open a file dialog. Navigate to and select the PDF 
	file you wish to modify.

3. Once loaded, the first page of the PDF will be displayed in the preview area. Use 
	the spin box above the preview to navigate to different pages.

4. To delete a page, navigate to the desired page using the spin box and click the 
	"Delete Page" button. The page will be marked for deletion, and the preview will 
 	update to reflect this.

5. You can continue to delete additional pages as needed.

6. Once you have marked all the pages you wish to delete, click the "Save Changes" button.
	This will save the modified PDF with a "_modified" suffix added to the original filename.

7. If you wish to work on a different PDF, simply click "Load PDF" again and repeat the
	process.

Note:
-------------
- The program always starts with the original PDF for each deletion to ensure accurate page deletion.
- The modified PDF is saved with a "_modified" suffix. The original PDF remains unchanged.

Dependencies:
-------------
To run the PDF Page Deleter program, you'll need to install the following Python packages:

1. PyQt5: Provides the graphical user interface.
Installation: `pip install PyQt5`
2. PyPDF2: Used for PDF processing.
Installation: `pip install PyPDF2`
3. PyMuPDF (fitz): Required for rendering PDF pages as images for the preview functionality.
Installation: `pip install PyMuPDF`

'''


import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QSpinBox, QVBoxLayout, QWidget, QTextEdit, QLabel, QSizePolicy, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter
import fitz

class PDFPageDeleterApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.init_ui()

	def init_ui(self):
		self.setWindowTitle('PDF Page Deleter')

		# Create widgets
		self.load_button = QPushButton('Load PDF', self)
		self.load_button.clicked.connect(self.load_pdf)

		self.page_spinbox = QSpinBox(self)
		self.page_spinbox.setMinimum(1)
		self.page_spinbox.valueChanged.connect(self.update_preview)

		self.delete_button = QPushButton('Delete Page', self)
		self.delete_button.clicked.connect(self.delete_page)

		self.preview_label = QLabel(self)
		self.preview_label.setAlignment(Qt.AlignCenter)
		self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
  
		self.save_button = QPushButton('Save Changes', self)
		self.save_button.clicked.connect(self.save_changes)

		self.status_area = QTextEdit(self)
		self.status_area.setReadOnly(True)

		# Control panel layout
		control_layout = QVBoxLayout()
		control_layout.addWidget(self.load_button)
		control_layout.addWidget(self.page_spinbox)
		control_layout.addWidget(self.delete_button)
		control_layout.addWidget(self.save_button)
		control_layout.addWidget(self.status_area)

		# Main layout
		main_layout = QHBoxLayout()
		main_layout.addLayout(control_layout, 1)  # Smaller portion
		main_layout.addWidget(self.preview_label, 3)  # Larger portion

		central_widget = QWidget()
		central_widget.setLayout(main_layout)
		self.setCentralWidget(central_widget)

		self.pdf_path = None
		self.pdf_document = None
		
		self.resize(800, 600)

	def load_pdf(self):
		options = QFileDialog.Options()
		file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)", options=options)
		if file_name:
			self.pdf_path = file_name
			self.pdf_document = fitz.open(file_name)
			self.page_spinbox.setMaximum(len(self.pdf_document))
			self.update_preview()
			self.status_area.append(f"Loaded PDF: {file_name}")
		self.modified_pdf = None


	def update_preview(self):
		if not self.pdf_document:
			return

		page_number = self.page_spinbox.value() - 1
		page = self.pdf_document[page_number]
		
		zoom_x = 3  # Adjust these values to get higher or lower resolution
		zoom_y = 3  # Adjust these values to get higher or lower resolution
		mat = fitz.Matrix(zoom_x, zoom_y)
		
		img = page.get_pixmap(matrix=mat)  # Use the matrix to adjust the resolution
		qt_img = QImage(img.samples, img.width, img.height, img.stride, QImage.Format_RGB888)
		pixmap = QPixmap.fromImage(qt_img)
		self.preview_label.setPixmap(pixmap.scaled(self.preview_label.width(), self.preview_label.height(), Qt.KeepAspectRatio))


	def delete_page(self):
		if not self.pdf_path:
			self.status_area.append("Please load a PDF first.")
			return

		page_number = self.page_spinbox.value()

		if not hasattr(self, 'pages_to_delete'):
			self.pages_to_delete = set()

		self.pages_to_delete.add(page_number)

		with open(self.pdf_path, 'rb') as f:
			reader = PdfReader(f)
			self.modified_pdf = PdfWriter()

			# Add all pages except the ones to be deleted
			for i, page in enumerate(reader.pages):
				if i + 1 not in self.pages_to_delete:
					self.modified_pdf.add_page(page)

		self.status_area.append(f"Page {page_number} marked for deletion.")
		self.page_spinbox.setMaximum(len(self.modified_pdf.pages) if self.modified_pdf else 0)
		self.update_preview()

	def save_changes(self):
		if not self.modified_pdf:
			self.status_area.append("No changes to save.")
			return

		new_pdf_path = self.pdf_path.replace('.pdf', '_modified.pdf')
		with open(new_pdf_path, 'wb') as out:
			self.modified_pdf.write(out)

		self.status_area.append(f"Changes saved as {new_pdf_path}.")
	def resizeEvent(self, event):
		self.update_preview()
		super().resizeEvent(event)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = PDFPageDeleterApp()
	window.show()
	sys.exit(app.exec_())
