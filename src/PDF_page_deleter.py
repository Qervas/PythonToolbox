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
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, 
    QSpinBox, QVBoxLayout, QWidget, QTextEdit, QLabel, 
    QSizePolicy, QHBoxLayout, QScrollArea, QShortcut, 
    QLineEdit, QTreeWidget, QListWidget, QDockWidget, 
    QTreeWidgetItem, QListWidgetItem, QAction, QInputDialog,
    QToolBar
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPalette, QColor, QKeySequence, 
    QPainter, QIcon
)
from PyQt5.QtCore import (
    Qt, QSettings, QTimer, QSize
)
from PyPDF2 import PdfReader, PdfWriter
import fitz
import os
from collections import OrderedDict

class PDFPageDeleterApp(QMainWindow):
	def __init__(self):
		super().__init__()
		# Initialize document-related attributes
		self.pdf_document = None
		self.pdf_path = None
		self.deleted_pages = set()
		self.modified_pdf = None
		
		# Initialize UI-related attributes
		self.zoom_level = 1.0
		self.is_dark_mode = QApplication.instance().palette().color(QPalette.Window).lightness() < 128
		self.current_search_index = 0
		self.search_results = []
		self.current_page = 1
		
		# Initialize caching
		self.page_cache = OrderedDict()
		self.max_cache_size = 20
		
		# Initialize settings
		self.settings = QSettings('YourCompany', 'PDFPageDeleter')
		self.last_directory = self.settings.value('last_directory', '')
		
		# Create menu bar first
		self.create_menu_bar()
		
		# Setup UI components
		self.setup_theme()
		self.init_ui()
		self.setup_shortcuts()
		
		# Initialize preview components
		self.continuous_preview = QLabel(self)
		self.continuous_preview.setAlignment(Qt.AlignCenter)
		
		# Setup render timer
		self.render_timer = QTimer()
		self.render_timer.setSingleShot(True)
		self.render_timer.timeout.connect(self.render_visible_pages)
		
		# Optimize scroll handling
		self.scroll_area.verticalScrollBar().valueChanged.connect(
			lambda: self.render_timer.start(150))  # Increased delay for better performance
		
		# Restore window state
		geometry = self.settings.value('geometry')
		if geometry:
			self.restoreGeometry(geometry)
		state = self.settings.value('windowState')
		if state:
			self.restoreState(state)

		# Connect scroll bar changes to page indicator update
		self.scroll_area.verticalScrollBar().valueChanged.connect(self.update_page_indicator)

	def setup_theme(self):
		app = QApplication.instance()
		palette = QPalette()
		
		if self.is_dark_mode:
			# Dark theme colors
			window_color = QColor(53, 53, 53)
			text_color = QColor(255, 255, 255)  # Changed from Qt.white
			button_color = QColor(75, 75, 75)
		else:
			# Light theme colors
			window_color = QColor(240, 240, 240)
			text_color = QColor(0, 0, 0)  # Changed from Qt.black
			button_color = QColor(225, 225, 225)
			
		palette.setColor(QPalette.Window, window_color)
		palette.setColor(QPalette.WindowText, text_color)
		palette.setColor(QPalette.Base, window_color.darker(120))
		palette.setColor(QPalette.AlternateBase, window_color)
		palette.setColor(QPalette.ToolTipBase, text_color)
		palette.setColor(QPalette.ToolTipText, text_color)
		palette.setColor(QPalette.Text, text_color)
		palette.setColor(QPalette.Button, button_color)
		palette.setColor(QPalette.ButtonText, text_color)
		palette.setColor(QPalette.BrightText, QColor(255, 0, 0))  # Changed from Qt.red
		palette.setColor(QPalette.Link, QColor(42, 130, 218))
		palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
		palette.setColor(QPalette.HighlightedText, window_color)
		
		app.setPalette(palette)

		# Update button styles for better visibility
		button_style = f"""
			QPushButton {{
				background-color: {button_color.name()};
				color: {text_color.name()};
				border: 1px solid {text_color.name()};
				padding: 5px;
				border-radius: 3px;
			}}
			QPushButton:hover {{
				background-color: {button_color.lighter(110).name()};
			}}
			QPushButton:pressed {{
				background-color: {button_color.darker(110).name()};
			}}
		"""
		app.setStyleSheet(button_style)

		# Add dock widget styling
		dock_style = """
			QDockWidget {
				border: 1px solid #555;
				titlebar-close-icon: url(close.png);
			}
			QDockWidget::title {
				background: %s;
				padding-left: 5px;
			}
			QDockWidget::close-button, QDockWidget::float-button {
				border: 1px solid transparent;
				background: %s;
				padding: 0px;
			}
			QDockWidget::close-button:hover, QDockWidget::float-button:hover {
				background: %s;
			}
		""" % (
			button_color.name(),
			window_color.name(),
			button_color.lighter(110).name()
		)
		
		app.setStyleSheet(button_style + dock_style)

	def init_ui(self):
		"""Initialize the UI with a modern, professional layout"""
		# Create main widget and layout
		main_widget = QWidget()
		self.setCentralWidget(main_widget)
		main_layout = QHBoxLayout(main_widget)
		main_layout.setSpacing(0)
		main_layout.setContentsMargins(0, 0, 0, 0)
		
		# Create modern toolbar
		toolbar = QToolBar()
		toolbar.setIconSize(QSize(24, 24))
		toolbar.setMovable(False)
		toolbar.setStyleSheet("""
			QToolBar {
				background: #2b2b2b;
				border: none;
				padding: 5px;
			}
			QPushButton {
				background: #3b3b3b;
				border: none;
				color: white;
				padding: 5px 10px;
				border-radius: 3px;
				margin: 0 2px;
			}
			QPushButton:hover {
				background: #4b4b4b;
			}
			QLabel {
				color: white;
				padding: 0 10px;
			}
		""")
		self.addToolBar(Qt.TopToolBarArea, toolbar)
		
		# Add zoom controls with modern icons
		self.zoom_out_btn = QPushButton('−')
		self.zoom_in_btn = QPushButton('+')
		self.zoom_fit_btn = QPushButton('⊡')  # Unicode for fit
		self.zoom_width_btn = QPushButton('↔')  # Unicode for width
		self.zoom_label = QLabel('100%')
		
		for btn in [self.zoom_out_btn, self.zoom_in_btn, 
					self.zoom_fit_btn, self.zoom_width_btn]:
			btn.setFixedSize(32, 32)
			toolbar.addWidget(btn)
		
		toolbar.addWidget(self.zoom_label)
		toolbar.addSeparator()
		
		# Add bookmark button with modern icon
		self.bookmark_btn = QPushButton('🔖')
		self.bookmark_btn.setFixedSize(32, 32)
		self.bookmark_btn.setToolTip("Toggle Bookmark (Ctrl+B)")
		toolbar.addWidget(self.bookmark_btn)
		
		# Add page indicator with modern style
		self.page_indicator = QLabel("Page 0/0")
		self.page_indicator.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.page_indicator.setMinimumWidth(150)
		toolbar.addWidget(self.page_indicator)
		
		# Create left sidebar for controls
		left_panel = QWidget()
		left_panel.setMaximumWidth(250)
		left_panel.setStyleSheet("""
			QWidget {
				background: #2b2b2b;
				color: white;
			}
			QPushButton {
				background: #3b3b3b;
				border: none;
				padding: 8px;
				border-radius: 4px;
				margin: 2px 0;
			}
			QPushButton:hover {
				background: #4b4b4b;
			}
			QSpinBox {
				background: #3b3b3b;
				border: none;
				padding: 5px;
				border-radius: 4px;
				color: white;
			}
		""")
		
		control_layout = QVBoxLayout(left_panel)
		control_layout.setContentsMargins(10, 10, 10, 10)
		control_layout.setSpacing(5)
		
		# Add controls with modern styling
		self.load_button = QPushButton('📂 Load PDF')
		self.page_spinbox = QSpinBox()
		self.delete_button = QPushButton('🗑️ Delete Page')
		self.save_button = QPushButton('💾 Save Changes')
		self.dark_mode_button = QPushButton('🌓 Toggle Theme')
		
		# Add status area with modern style
		self.status_area = QTextEdit()
		self.status_area.setReadOnly(True)
		self.status_area.setMaximumHeight(100)
		self.status_area.setStyleSheet("""
			QTextEdit {
				background: #333333;
				border: none;
				border-radius: 4px;
				color: #cccccc;
				padding: 5px;
			}
		""")
		
		# Add widgets to control layout
		for widget in [self.load_button, self.page_spinbox, self.delete_button,
					  self.save_button, self.dark_mode_button, self.status_area]:
			control_layout.addWidget(widget)
		
		# Create modern scroll area for PDF preview
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setStyleSheet("""
			QScrollArea {
				background: #1e1e1e;
				border: none;
			}
			QScrollBar {
				background: #2b2b2b;
				width: 12px;
				border: none;
			}
			QScrollBar::handle {
				background: #4b4b4b;
				border-radius: 6px;
				min-height: 30px;
			}
			QScrollBar::handle:hover {
				background: #5b5b5b;
			}
		""")
		
		# Create content widget for scroll area
		self.scroll_content = QWidget()
		self.scroll_layout = QVBoxLayout(self.scroll_content)
		self.scroll_layout.setAlignment(Qt.AlignCenter)
		self.scroll_area.setWidget(self.scroll_content)
		
		# Create preview label
		self.preview_label = QLabel()
		self.preview_label.setAlignment(Qt.AlignCenter)
		self.scroll_layout.addWidget(self.preview_label)
		
		# Add panels to main layout
		main_layout.addWidget(left_panel)
		main_layout.addWidget(self.scroll_area, stretch=1)
		
		# Create dock widgets with modern style
		self.create_dock_widgets()
		
		# Connect signals
		self.setup_connections()
		
		# Set window properties
		self.setWindowTitle('PDF Page Deleter')
		self.setGeometry(100, 100, 1200, 800)

	def create_dock_widgets(self):
			"""Create modern styled dock widgets with proper object names"""
			dock_style = """
				QDockWidget {
					border: none;
					background: #2b2b2b;
					color: white;
				}
				QDockWidget::title {
					background: #3b3b3b;
					padding: 5px;
				}
				QTreeWidget, QListWidget {
					background: #2b2b2b;
					border: none;
					color: white;
				}
				QTreeWidget::item:hover, QListWidget::item:hover {
					background: #3b3b3b;
				}
				QTreeWidget::item:selected, QListWidget::item:selected {
					background: #4b4b4b;
				}
			"""
			
			# Table of Contents dock
			toc_dock = QDockWidget("📚 Table of Contents", self)
			toc_dock.setObjectName("toc_dock")
			self.toc_widget = QTreeWidget()
			self.toc_widget.setUniformRowHeights(True)  # Performance optimization
			self.toc_widget.setHeaderLabel("Contents")
			toc_dock.setWidget(self.toc_widget)
			toc_dock.setStyleSheet(dock_style)
			
			# Thumbnails dock
			thumb_dock = QDockWidget("🖼️ Thumbnails", self)
			thumb_dock.setObjectName("thumb_dock")
			self.thumbnail_widget = QListWidget()
			self.thumbnail_widget.setViewMode(QListWidget.IconMode)
			self.thumbnail_widget.setIconSize(QSize(100, 140))  # Smaller thumbnails
			self.thumbnail_widget.setSpacing(10)
			self.thumbnail_widget.setResizeMode(QListWidget.Adjust)
			self.thumbnail_widget.setUniformItemSizes(True)  # Performance optimization
			thumb_dock.setWidget(self.thumbnail_widget)
			thumb_dock.setStyleSheet(dock_style)
			
			# Bookmarks dock
			bookmark_dock = QDockWidget("🔖 Bookmarks", self)
			bookmark_dock.setObjectName("bookmark_dock")
			self.bookmark_widget = QListWidget()
			bookmark_dock.setWidget(self.bookmark_widget)
			bookmark_dock.setStyleSheet(dock_style)
			
			# Add docks to main window
			self.addDockWidget(Qt.LeftDockWidgetArea, toc_dock)
			self.addDockWidget(Qt.LeftDockWidgetArea, thumb_dock)
			self.addDockWidget(Qt.LeftDockWidgetArea, bookmark_dock)

	def adjust_zoom(self, factor):
		"""Smart zoom with center point preservation"""
		old_pos = self.scroll_area.verticalScrollBar().value()
		viewport_height = self.scroll_area.viewport().height()
		center_y = old_pos + viewport_height / 2
		
		old_zoom = self.zoom_level
		self.zoom_level *= factor
		self.zoom_level = max(0.1, min(5.0, self.zoom_level))  # Limit zoom range
		
		# Update zoom indicator
		self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
		
		# Clear cache to force redraw
		self.page_cache.clear()
		self.render_visible_pages()
		
		# Maintain center point
		new_pos = int((center_y * self.zoom_level / old_zoom) - viewport_height / 2)
		self.scroll_area.verticalScrollBar().setValue(new_pos)

	def zoom_to_fit(self):
		"""Zoom to fit page height"""
		if not self.pdf_document:
			return
		
		page = self.pdf_document[0]
		viewport_height = self.scroll_area.viewport().height()
		page_height = page.rect.height
		
		self.zoom_level = (viewport_height / page_height) * 0.9  # 90% of viewport
		self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
		self.page_cache.clear()
		self.render_visible_pages()

	def zoom_to_width(self):
		"""Zoom to fit page width"""
		if not self.pdf_document:
			return
		
		page = self.pdf_document[0]
		viewport_width = self.scroll_area.viewport().width()
		page_width = page.rect.width
		
		self.zoom_level = (viewport_width / page_width) * 0.95  # 95% of viewport
		self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
		self.page_cache.clear()
		self.render_visible_pages()

	def get_visible_pages(self):
		"""Get list of currently visible pages with dynamic page size handling"""
		if not self.pdf_document or not self.scroll_layout:
			return []
		
		try:
			scroll_bar = self.scroll_area.verticalScrollBar()
			viewport_top = scroll_bar.value()
			viewport_height = self.scroll_area.viewport().height()
			viewport_bottom = viewport_top + viewport_height
			visible_pages = []
			
			total_height = 0
			for i in range(self.scroll_layout.count()):
				widget = self.scroll_layout.itemAt(i).widget()
				if not widget:
					continue
					
				widget_height = widget.height()
				widget_top = total_height
				widget_bottom = total_height + widget_height
				
				# A page is considered visible if:
				# 1. Its top is in the viewport, OR
				# 2. Its bottom is in the viewport, OR
				# 3. It spans the viewport
				is_visible = (
					(widget_top >= viewport_top and widget_top < viewport_bottom) or
					(widget_bottom > viewport_top and widget_bottom <= viewport_bottom) or
					(widget_top <= viewport_top and widget_bottom >= viewport_bottom)
				)
				
				if is_visible:
					visible_pages.append(i)
					
				total_height += widget_height
				
				# Optimization: Stop if we're past the viewport
				if widget_top > viewport_bottom:
					break
			
			return visible_pages
		except Exception as e:
			print(f"Error getting visible pages: {e}")
			return []

	def render_visible_pages(self):
		"""
		Efficiently render only the visible pages in the scroll area
		with robust error handling and performance optimizations.
		"""
		if not self.pdf_document or not self.scroll_layout:
			return

		try:
			# Get viewport metrics
			viewport = self.scroll_area.viewport()
			scroll_pos = self.scroll_area.verticalScrollBar().value()
			viewport_height = viewport.height()
			
			# Performance optimization: Calculate page metrics once
			PAGE_MARGIN = 20
			BUFFER_PAGES = 1  # Number of pages to pre-render above/below viewport
			
			# Get actual page height from first page if available
			actual_page_height = viewport_height
			if self.scroll_layout.count() > 0:
				first_container = self.scroll_layout.itemAt(0).widget()
				if first_container and first_container.height() > 0:
					actual_page_height = first_container.height() + PAGE_MARGIN

			# Calculate visible page range with buffer
			first_visible = max(0, (scroll_pos // actual_page_height) - BUFFER_PAGES)
			last_visible = min(
				len(self.pdf_document),
				((scroll_pos + viewport_height) // actual_page_height) + BUFFER_PAGES + 1
			)

			# Debug logging for development
			# print(f"Rendering pages {first_visible} to {last_visible}")
			
			# Batch render visible pages
			for page_num in range(int(first_visible), int(last_visible)):
				if not (0 <= page_num < self.scroll_layout.count()):
					continue
					
				# Get container widget safely
				container_item = self.scroll_layout.itemAt(page_num)
				if not container_item:
					continue
					
				container = container_item.widget()
				if not container or not container.layout():
					continue
				
				# Find the page label in the container
				layout = container.layout()
				for i in range(layout.count()):
					widget = layout.itemAt(i).widget()
					if isinstance(widget, QLabel) and not widget.pixmap():
						# Only render if not already rendered
						self.render_page(page_num)
						break

			# Cleanup far-off pages to save memory
			cleanup_range = 5  # Pages to keep beyond visible range
			for page_num in range(len(self.pdf_document)):
				if (page_num < first_visible - cleanup_range or 
					page_num > last_visible + cleanup_range):
					if page_num in self.page_cache:
						del self.page_cache[page_num]

		except Exception as e:
			import traceback
			print(f"Render error: {str(e)}")
			print(traceback.format_exc())
			# Prevent rapid re-rendering on error
			self.render_timer.stop()

	def render_page(self, page_num):
		"""Render page with proper scaling"""
		if not self.pdf_document or page_num >= len(self.pdf_document):
			return
		
		try:
			if page_num in self.page_cache:
				pixmap = self.page_cache[page_num]
			else:
				page = self.pdf_document[page_num]
				zoom = 2.0 * self.zoom_level  # Increased resolution for better quality
				mat = fitz.Matrix(zoom, zoom)
				pix = page.get_pixmap(matrix=mat, alpha=False)
				
				img = QImage(pix.samples, pix.width, pix.height,
							pix.stride, QImage.Format_RGB888)
				
				if self.is_dark_mode:
					img.invertPixels()
				
				pixmap = QPixmap.fromImage(img)
				
				if len(self.page_cache) > self.max_cache_size:
					self.page_cache.popitem(last=False)
				self.page_cache[page_num] = pixmap
			
			# Update the label with scaled pixmap
			if self.scroll_layout and self.scroll_layout.count() > page_num:
				container = self.scroll_layout.itemAt(page_num).widget()
				if container:
					for i in range(container.layout().count()):
						widget = container.layout().itemAt(i).widget()
						if isinstance(widget, QLabel) and widget.objectName().startswith('page_label'):
							scaled_pixmap = pixmap.scaled(widget.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
							widget.setPixmap(scaled_pixmap)
							break
							
		except Exception as e:
			print(f"Page rendering error: {e}")

	def update_page_indicator(self):
		"""Update the page indicator with better multi-page detection"""
		if not self.pdf_document:
			return
		
		try:
			visible_pages = self.get_visible_pages()
			if visible_pages:
				start_page = min(visible_pages) + 1
				end_page = max(visible_pages) + 1
				total_pages = len(self.pdf_document)
				zoom_text = f"Zoom: {int(self.zoom_level * 100)}%"
				
				# Always show range if multiple pages are visible
				if len(visible_pages) > 1:
					text = f"Pages {start_page}-{end_page}/{total_pages} {zoom_text}"
				else:
					text = f"Page {start_page}/{total_pages} {zoom_text}"
				
				self.page_indicator.setText(text)
				# Update spinbox to most visible page
				most_visible_page = self.get_most_visible_page(visible_pages)
				if most_visible_page is not None:
					self.page_spinbox.setValue(most_visible_page + 1)
		except Exception as e:
			print(f"Error updating page indicator: {e}")

	def get_most_visible_page(self, visible_pages):
		"""Determine which page is most visible in the viewport"""
		if not visible_pages:
			return None
			
		try:
			viewport_top = self.scroll_area.verticalScrollBar().value()
			viewport_height = self.scroll_area.viewport().height()
			viewport_center = viewport_top + (viewport_height / 2)
			
			# Find page whose center is closest to viewport center
			best_page = None
			min_distance = float('inf')
			
			total_height = 0
			for i in range(self.scroll_layout.count()):
				if i not in visible_pages:
					continue
					
				widget = self.scroll_layout.itemAt(i).widget()
				if not widget:
					continue
					
				widget_height = widget.height()
				widget_center = total_height + (widget_height / 2)
				distance = abs(viewport_center - widget_center)
				
				if distance < min_distance:
					min_distance = distance
					best_page = i
					
				total_height += widget_height
			
			return best_page
		except Exception as e:
			print(f"Error finding most visible page: {e}")
			return visible_pages[0] if visible_pages else None

	def search_text(self):
		text = self.search_input.text()
		if not text or not self.pdf_document:
			return
			
		self.search_results = []
		for page_num in range(len(self.pdf_document)):
			page = self.pdf_document[page_num]
			instances = page.search_for(text)
			if instances:
				self.search_results.extend([(page_num, inst) for inst in instances])
		
		if self.search_results:
			self.navigate_search(True)

	def navigate_search(self, forward=True):
		if not self.search_results:
			return
			
		if forward:
			self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
		else:
			self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
			
		page_num, rect = self.search_results[self.current_search_index]
		self.page_spinbox.setValue(page_num + 1)
		# Highlight the search result
		self.highlight_search_result(page_num, rect)

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

	def setup_shortcuts(self):
		"""Setup keyboard shortcuts"""
		shortcuts = {
			"Ctrl+O": self.load_pdf,
			"Ctrl+S": self.save_changes,
			"Ctrl+Q": self.close,
			"Ctrl+B": self.toggle_bookmark,
			"Ctrl++": lambda: self.adjust_zoom(1.2),
			"Ctrl+-": lambda: self.adjust_zoom(0.8),
			"Ctrl+0": self.zoom_to_fit,
			"Ctrl+W": self.zoom_to_width,
			"Ctrl+G": self.goto_page_dialog,
			"F11": self.toggle_fullscreen,
		}
		
		for key, func in shortcuts.items():
			QShortcut(QKeySequence(key), self).activated.connect(func)

	def zoom_in(self):
		self.zoom_level *= 1.2
		self.update_preview()

	def zoom_out(self):
		self.zoom_level /= 1.2
		self.update_preview()

	def zoom_reset(self):
		self.zoom_level = 1.0
		self.update_preview()

	def next_page(self):
		if self.pdf_document and self.page_spinbox.value() < len(self.pdf_document):
			self.page_spinbox.setValue(self.page_spinbox.value() + 1)

	def prev_page(self):
		if self.pdf_document and self.page_spinbox.value() > 1:
			self.page_spinbox.setValue(self.page_spinbox.value() - 1)

	def first_page(self):
		if self.pdf_document:
			self.page_spinbox.setValue(1)

	def last_page(self):
		if self.pdf_document:
			self.page_spinbox.setValue(len(self.pdf_document))

	def wheelEvent(self, event):
		if event.modifiers() & Qt.ControlModifier:
			# Zoom with Ctrl + Mouse Wheel
			if event.angleDelta().y() > 0:
				self.zoom_in()
			else:
				self.zoom_out()
			event.accept()
		else:
			super().wheelEvent(event)

	def toggle_dark_mode(self):
		"""Toggle between light and dark mode"""
		self.is_dark_mode = not self.is_dark_mode
		self.setup_theme()
		
		# Clear cache to force re-render with new colors
		self.page_cache.clear()
		
		# Re-render current view
		self.update_preview()
		self.generate_thumbnails()  # Regenerate thumbnails with new theme

	def update_preview(self):
		"""Update the preview when page number changes"""
		if not hasattr(self, 'pdf_document') or not self.pdf_document:
			return
		
		try:
			page_number = self.page_spinbox.value() - 1
			if 0 <= page_number < len(self.pdf_document):
				self.render_page(page_number)
				self.update_page_indicator()
		except Exception as e:
			print(f"Preview update error: {e}")

	def load_toc(self):
		"""Load table of contents with proper hierarchy"""
		self.toc_widget.clear()
		if not self.pdf_document:
			return
		
		try:
			toc = self.pdf_document.get_toc()
			if not toc:
				self.toc_widget.addTopLevelItem(QTreeWidgetItem(["No table of contents"]))
				return
			
			# Create a dictionary to store parent items by level
			level_parents = {-1: self.toc_widget}
			prev_level = -1
			
			for item in toc:
				level, title, page = item[0], item[1], item[2]
				toc_item = QTreeWidgetItem([f"{title} (Page {page})"])
				
				# Find proper parent
				parent_level = level - 1
				while parent_level not in level_parents and parent_level > -1:
					parent_level -= 1
				parent = level_parents[parent_level]
				
				# Add item to tree
				if isinstance(parent, QTreeWidget):
					parent.addTopLevelItem(toc_item)
				else:
					parent.addChild(toc_item)
				
				# Store as potential parent for next items
				level_parents[level] = toc_item
				
				# Clean up old levels
				if level <= prev_level:
					for l in list(level_parents.keys()):
						if l > level:
							del level_parents[l]
				prev_level = level
			
			# Expand first level
			self.toc_widget.expandToDepth(0)
			
		except Exception as e:
			print(f"TOC loading error: {e}")
			self.toc_widget.addTopLevelItem(QTreeWidgetItem(["Error loading table of contents"]))

	def generate_thumbnails(self):
		"""Generate thumbnails for all pages"""
		self.thumbnail_widget.clear()
		
		if not self.pdf_document:
			return
		
		for page_num in range(len(self.pdf_document)):
			try:
				page = self.pdf_document[page_num]
				pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
				img = QImage(pix.samples, pix.width, pix.height,
							pix.stride, QImage.Format_RGB888)
				
				if self.is_dark_mode:
					img.invertPixels()
					
				pixmap = QPixmap.fromImage(img)
				
				# Create item with thumbnail
				item = QListWidgetItem()
				item.setIcon(QIcon(pixmap))
				item.setData(Qt.UserRole, page_num)  # Store page number in item data
				item.setText(f"Page {page_num + 1}")
				self.thumbnail_widget.addItem(item)
				
			except Exception as e:
				print(f"Thumbnail generation error for page {page_num}: {e}")

	def navigate_to_section(self, item):
		"""Navigate to section from table of contents"""
		try:
			# Extract page number from the text (Page X)
			text = item.text(0)  # Get the full text from first column
			page_str = text.split("(Page ")[-1].split(")")[0]
			page = int(page_str)
			
			# Update spinbox
			self.page_spinbox.setValue(page)
			
			# Find and scroll to the target container
			for i in range(self.scroll_layout.count()):
				container = self.scroll_layout.itemAt(i).widget()
				if container and container.objectName() == f"page_container_{page-1}":
					self.scroll_area.ensureWidgetVisible(container)
					break
					
		except Exception as e:
			print(f"Navigation error: {e}")

	def navigate_to_thumbnail(self, item):
		"""Navigate to the page when thumbnail is clicked"""
		try:
			page_num = item.data(Qt.UserRole)
			if page_num is not None:
				# Update spinbox
				self.page_spinbox.setValue(page_num + 1)
				
				# Find and scroll to the target container
				for i in range(self.scroll_layout.count()):
					container = self.scroll_layout.itemAt(i).widget()
					if container and container.objectName() == f"page_container_{page_num}":
						self.scroll_area.ensureWidgetVisible(container)
						break
						
				self.update_preview()
		except Exception as e:
			print(f"Navigation error: {e}")

	def navigate_to_bookmark(self, item):
		"""Navigate to bookmarked page"""
		page_num = item.data(Qt.UserRole)
		self.page_spinbox.setValue(page_num + 1)

	def toggle_bookmark(self):
		"""Toggle bookmark for current page"""
		if not self.pdf_document:
			return
		current_page = self.page_spinbox.value() - 1
		# Check if page is already bookmarked
		for i in range(self.bookmark_widget.count()):
			item = self.bookmark_widget.item(i)
			if item.data(Qt.UserRole) == current_page:
				self.bookmark_widget.takeItem(i)
				return
		# Add new bookmark
		item = QListWidgetItem(f"Page {current_page + 1}")
		item.setData(Qt.UserRole, current_page)
		self.bookmark_widget.addItem(item)

	def toggle_fullscreen(self):
		"""Toggle fullscreen mode"""
		if self.isFullScreen():
			self.showNormal()
		else:
			self.showFullScreen()

	def highlight_search_result(self, page_num, rect):
		"""Highlight search result in the preview"""
		if page_num in self.page_cache:
			# Create a copy of the cached page
			pixmap = self.page_cache[page_num].copy()
			painter = QPainter(pixmap)
			painter.setPen(QColor(255, 255, 0, 127))  # Semi-transparent yellow
			painter.drawRect(rect.x0, rect.y0, rect.width, rect.height)
			painter.end()
			
			# Update the display
			self.scroll_layout.itemAt(page_num).widget().setPixmap(pixmap)

	def add_to_recent_files(self, file_path):
		"""Add file to recent files list"""
		recent_files = self.settings.value('recent_files', [])
		if not isinstance(recent_files, list):
			recent_files = []
			
		# Add new file to start of list
		if file_path in recent_files:
			recent_files.remove(file_path)
		recent_files.insert(0, file_path)
		
		# Keep only last 10 files
		recent_files = recent_files[:10]
		
		# Save updated list
		self.settings.setValue('recent_files', recent_files)
		
		# Update recent files menu
		self.update_recent_files_menu()

	def update_recent_files_menu(self):
		"""Update the recent files menu"""
		self.recent_files_menu.clear()
		recent_files = self.settings.value('recent_files', [])
		if not isinstance(recent_files, list):
			recent_files = []
		
		for file_path in recent_files:
			if os.path.exists(file_path):  # Only show existing files
				action = self.recent_files_menu.addAction(os.path.basename(file_path))
				action.setStatusTip(file_path)
				action.triggered.connect(lambda checked, path=file_path: self.open_recent_file(path))

	def open_recent_file(self, file_path):
		"""Open a file from recent files list"""
		if os.path.exists(file_path):
			self.pdf_path = file_path
			self.pdf_document = fitz.open(file_path)
			self.load_toc()
			self.generate_thumbnails()
			self.setup_continuous_view()
			self.update_status_bar()
			self.status_area.append(f"Loaded PDF: {file_path}")
		else:
			self.status_area.append(f"Error: File not found: {file_path}")
			# Remove non-existent file from recent files
			recent_files = self.settings.value('recent_files', [])
			if file_path in recent_files:
				recent_files.remove(file_path)
				self.settings.setValue('recent_files', recent_files)
				self.update_recent_files_menu()

	def clear_recent_files(self):
		"""Clear the recent files list"""
		self.settings.setValue('recent_files', [])
		self.update_recent_files_menu()

	def closeEvent(self, event):
		"""Save settings when closing the application"""
		# Save window geometry
		self.settings.setValue('geometry', self.saveGeometry())
		self.settings.setValue('windowState', self.saveState())
		super().closeEvent(event)

	def create_menu_bar(self):
		"""Create menu bar and menus"""
		menubar = self.menuBar()
		
		# File menu
		file_menu = menubar.addMenu('File')
		
		# Open action
		open_action = QAction('Open', self)
		open_action.setShortcut('Ctrl+O')
		open_action.triggered.connect(self.load_pdf)
		file_menu.addAction(open_action)
		
		# Create Recent Files menu
		self.recent_files_menu = file_menu.addMenu('Recent Files')
		
		# Clear recent action
		clear_recent_action = QAction('Clear Recent Files', self)
		clear_recent_action.triggered.connect(self.clear_recent_files)
		file_menu.addAction(clear_recent_action)
		
		file_menu.addSeparator()
		
		# Save action
		save_action = QAction('Save', self)
		save_action.setShortcut('Ctrl+S')
		save_action.triggered.connect(self.save_changes)
		file_menu.addAction(save_action)
		
		file_menu.addSeparator()
		
		# Exit action
		exit_action = QAction('Exit', self)
		exit_action.setShortcut('Ctrl+Q')
		exit_action.triggered.connect(self.close)
		file_menu.addAction(exit_action)
		
		# View menu
		view_menu = menubar.addMenu('View')
		
		# Add zoom actions
		zoom_in_action = QAction('Zoom In', self)
		zoom_in_action.setShortcut('Ctrl++')
		zoom_in_action.triggered.connect(lambda: self.adjust_zoom(1.2))
		view_menu.addAction(zoom_in_action)
		
		zoom_out_action = QAction('Zoom Out', self)
		zoom_out_action.setShortcut('Ctrl+-')
		zoom_out_action.triggered.connect(lambda: self.adjust_zoom(0.8))
		view_menu.addAction(zoom_out_action)
		
		# Update recent files menu
		self.update_recent_files_menu()

	def goto_page_dialog(self):
		"""Quick page navigation dialog"""
		if not self.pdf_document:
			return
		
		page, ok = QInputDialog.getInt(
			self, "Go to Page", "Enter page number:",
			self.page_spinbox.value(), 1, len(self.pdf_document)
		)
		if ok:
			self.page_spinbox.setValue(page)

	def setup_connections(self):
		"""Setup signal connections for all UI elements"""
		# Zoom controls
		self.zoom_out_btn.clicked.connect(lambda: self.adjust_zoom(0.8))
		self.zoom_in_btn.clicked.connect(lambda: self.adjust_zoom(1.2))
		self.zoom_fit_btn.clicked.connect(self.zoom_to_fit)
		self.zoom_width_btn.clicked.connect(self.zoom_to_width)
		
		# Main controls
		self.load_button.clicked.connect(self.load_pdf)
		self.page_spinbox.valueChanged.connect(self.update_preview)
		self.delete_button.clicked.connect(self.delete_page)
		self.save_button.clicked.connect(self.save_changes)
		self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
		self.bookmark_btn.clicked.connect(self.toggle_bookmark)
		
		# Dock widget connections
		self.toc_widget.itemClicked.connect(self.navigate_to_section)
		self.thumbnail_widget.itemClicked.connect(self.navigate_to_thumbnail)
		self.bookmark_widget.itemClicked.connect(self.navigate_to_bookmark)
		
		# Scroll area connection
		self.scroll_area.verticalScrollBar().valueChanged.connect(
			lambda: self.render_timer.start(100))

	def load_pdf(self):
		"""Load a PDF file"""
		file_name, _ = QFileDialog.getOpenFileName(
			self,
			"Open PDF",
			self.last_directory,
			"PDF files (*.pdf)"
		)
		
		if file_name:
			try:
				# Save directory for next time
				self.last_directory = os.path.dirname(file_name)
				self.settings.setValue('last_directory', self.last_directory)
				
				# Close existing document if any
				if self.pdf_document:
					self.pdf_document.close()
				
				# Open new document
				self.pdf_document = fitz.open(file_name)
				self.pdf_path = file_name
				self.deleted_pages = set()
				self.modified_pdf = None
				
				# Clear cache
				self.page_cache.clear()
				
				# Update UI
				self.page_spinbox.setMaximum(len(self.pdf_document))
				self.page_spinbox.setValue(1)
				
				# Load document components
				self.load_toc()
				self.generate_thumbnails()
				self.setup_continuous_view()
				
				# Add to recent files
				self.add_to_recent_files(file_name)
				
				# Update status
				self.status_area.append(f"Loaded PDF: {file_name}")
				self.update_page_indicator()
				
			except Exception as e:
				self.status_area.append(f"Error loading PDF: {str(e)}")
				if self.pdf_document:
					self.pdf_document.close()
				self.pdf_document = None
				self.pdf_path = None

	def setup_continuous_view(self):
		"""Setup continuous view with full content visibility"""
		if not self.pdf_document:
			return
		
		self.scroll_area.verticalScrollBar().blockSignals(True)
		
		# Clear existing layout
		while self.scroll_layout.count():
			item = self.scroll_layout.takeAt(0)
			if item.widget():
				item.widget().deleteLater()
		
		# Calculate proper sizes based on viewport
		viewport_width = self.scroll_area.viewport().width()
		
		# Create containers for each page
		for page_num in range(len(self.pdf_document)):
			page = self.pdf_document[page_num]
			page_rect = page.rect
			
			# Calculate scale factor based on width while preserving aspect ratio
			scale_factor = (viewport_width - 60) / page_rect.width
			
			# Calculate dimensions
			page_width = int(page_rect.width * scale_factor)
			page_height = int(page_rect.height * scale_factor)
			
			# Create container with flexible height
			container = QWidget()
			container.setFixedWidth(viewport_width - 20)
			
			layout = QVBoxLayout(container)
			layout.setSpacing(5)
			layout.setContentsMargins(5, 5, 5, 5)
			
			container.setObjectName(f"page_container_{page_num}")
			
			# Page number label
			num_label = QLabel(f"Page {page_num + 1}")
			num_label.setAlignment(Qt.AlignCenter)
			num_label.setStyleSheet("QLabel { color: gray; }")
			layout.addWidget(num_label)
			
			# Page content label with proper sizing
			page_label = QLabel()
			page_label.setAlignment(Qt.AlignCenter)
			page_label.setFixedSize(page_width, page_height)  # Use fixed size instead of minimum/maximum
			page_label.setObjectName(f"page_label_{page_num}")
			layout.addWidget(page_label)
			
			# Ensure container can accommodate the content
			container.setMinimumHeight(page_height + 40)  # Add padding for page number
			
			self.scroll_layout.addWidget(container)
		
		# Set content size
		self.scroll_content.setFixedWidth(viewport_width)
		total_height = sum(self.scroll_layout.itemAt(i).widget().minimumHeight() + 10
						  for i in range(self.scroll_layout.count()))
		self.scroll_content.setMinimumHeight(total_height)
		
		self.scroll_area.verticalScrollBar().blockSignals(False)
		QTimer.singleShot(50, self.render_visible_pages)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = PDFPageDeleterApp()
	window.show()
	sys.exit(app.exec_())

