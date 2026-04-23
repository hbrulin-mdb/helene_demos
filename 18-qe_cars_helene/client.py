import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QSpinBox, QComboBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

class VehicleClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vehicle Database Manager")
        self.resize(1000, 700) # Increased default size to accommodate the table better

        # Default Settings
        self.server_url = "http://localhost:8000"
        self.current_font_size = 10

        # Main Widget and Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Setup Tabs
        self.setup_search_tab()
        self.setup_insert_tab()
        self.setup_settings_tab()

        # Apply initial settings
        self.apply_font_size()
        
        # Initial data fetch for the insert tab table
        self.fetch_latest_documents()

    def setup_search_tab(self):
        search_tab = QWidget()
        layout = QVBoxLayout(search_tab)

        # Search Controls
        search_controls_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Start typing to search...")
        
        search_controls_layout.addWidget(QLabel("Search term:"))
        search_controls_layout.addWidget(self.search_input)
        
        layout.addLayout(search_controls_layout)

        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(10)
        self.results_table.setHorizontalHeaderLabels([
            "ID", "VIN", "License Plate", "Version", "Model", 
            "Name", "Manufacturer", "Energy Source", "Type", "Kilometres"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.results_table)

        self.tabs.addTab(search_tab, "Search")

        # Debounce Timer for dynamic searching
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # Connect signals
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.textChanged.connect(self.perform_search)

    def setup_insert_tab(self):
        insert_tab = QWidget()
        layout = QVBoxLayout(insert_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Controls
        controls_layout = QHBoxLayout()
        
        self.insert_count_spinbox = QSpinBox()
        self.insert_count_spinbox.setRange(1, 100000)
        self.insert_count_spinbox.setValue(1000)
        
        self.insert_button = QPushButton("Insert Documents")
        self.insert_button.clicked.connect(self.perform_insert)
        
        self.refresh_button = QPushButton("Refresh Table")
        self.refresh_button.clicked.connect(self.fetch_latest_documents)

        controls_layout.addWidget(QLabel("Number of Documents:"))
        controls_layout.addWidget(self.insert_count_spinbox)
        controls_layout.addWidget(self.insert_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)
        
        self.insert_status_label = QLabel("")
        layout.addWidget(self.insert_status_label)

        # Database Preview Table
        self.insert_table = QTableWidget()
        self.insert_table.setColumnCount(10)
        self.insert_table.setHorizontalHeaderLabels([
            "ID", "VIN", "License Plate", "Version", "Model", 
            "Name", "Manufacturer", "Energy Source", "Type", "Kilometres"
        ])
        self.insert_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.insert_table)

        self.tabs.addTab(insert_tab, "Insert")

    def setup_settings_tab(self):
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # URL Setting
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit(self.server_url)
        url_layout.addWidget(QLabel("Server URL:"))
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Font Setting
        font_layout = QHBoxLayout()
        self.font_spinbox = QSpinBox()
        self.font_spinbox.setRange(8, 36)
        self.font_spinbox.setValue(self.current_font_size)
        font_layout.addWidget(QLabel("UI Font Size:"))
        font_layout.addWidget(self.font_spinbox)
        font_layout.addStretch()
        layout.addLayout(font_layout)

        # Apply Button
        self.apply_settings_btn = QPushButton("Apply Settings")
        self.apply_settings_btn.clicked.connect(self.apply_settings)
        layout.addWidget(self.apply_settings_btn)

        self.tabs.addTab(settings_tab, "Settings")

    # --- Actions ---

    def on_search_text_changed(self):
        self.search_timer.start(500)

    def perform_search(self):
        search_text = self.search_input.text().strip()

        if not search_text or len(search_text) < 3:
            self.results_table.setRowCount(0)
            return
        print(f"Search text: {search_text}")

        payload = {"term": search_text.upper()}
        
        try:
            response = requests.post(f"{self.server_url}/search", json=payload)
            response.raise_for_status()
            data = response.json()
            self.populate_table(self.results_table, data)
        except requests.exceptions.RequestException as e:
            self.results_table.setRowCount(0)
            print(f"Search error: {e}")
            
    def fetch_latest_documents(self):
        """Fetches the top 1000 documents for the insert tab preview."""
        self.insert_status_label.setText("Fetching latest documents...")
        QApplication.processEvents()
        
        try:
            response = requests.get(f"{self.server_url}/vehicles?limit=1000")
            response.raise_for_status()
            data = response.json()
            self.populate_table(self.insert_table, data)
            self.insert_status_label.setText(f"Showing {len(data)} documents.")
        except requests.exceptions.RequestException as e:
            self.insert_status_label.setText("Error fetching documents.")
            print(f"Fetch error: {e}")

    def populate_table(self, table_widget, data):
        """Generic method to populate a given QTableWidget with document data."""
        table_widget.setRowCount(len(data))
        for row_idx, doc in enumerate(data):
            table_widget.setItem(row_idx, 0, QTableWidgetItem(str(doc.get("_id", ""))))
            table_widget.setItem(row_idx, 1, QTableWidgetItem(str(doc.get("VIN", ""))))
            table_widget.setItem(row_idx, 2, QTableWidgetItem(str(doc.get("licensePlate", ""))))
            table_widget.setItem(row_idx, 3, QTableWidgetItem(str(doc.get("version", ""))))
            table_widget.setItem(row_idx, 4, QTableWidgetItem(str(doc.get("model", ""))))
            table_widget.setItem(row_idx, 5, QTableWidgetItem(str(doc.get("name", ""))))
            table_widget.setItem(row_idx, 6, QTableWidgetItem(str(doc.get("manufacturer", ""))))
            table_widget.setItem(row_idx, 7, QTableWidgetItem(str(doc.get("energySource", ""))))
            table_widget.setItem(row_idx, 8, QTableWidgetItem(str(doc.get("vehicleType", ""))))
            table_widget.setItem(row_idx, 9, QTableWidgetItem(str(doc.get("kilometres", ""))))

    def perform_insert(self):
        count = self.insert_count_spinbox.value()
        self.insert_button.setEnabled(False)
        self.insert_status_label.setText("Inserting documents, please wait...")
        QApplication.processEvents() 

        try:
            response = requests.post(f"{self.server_url}/generate/{count}")
            response.raise_for_status()
            data = response.json()
            inserted_count = data.get("inserted_count", 0)
            self.insert_status_label.setText(f"Successfully inserted {inserted_count} documents.")
            
            # Auto-refresh the table to show the newly inserted documents
            self.fetch_latest_documents()
            
        except requests.exceptions.RequestException as e:
            self.insert_status_label.setText("Error occurred during insertion.")
            QMessageBox.critical(self, "Error", f"Failed to insert documents:\n{e}")
        finally:
            self.insert_button.setEnabled(True)

    def apply_settings(self):
        self.server_url = self.url_input.text().strip().rstrip('/')
        self.current_font_size = self.font_spinbox.value()
        self.apply_font_size()
        # Fetch docs again in case the URL changed
        self.fetch_latest_documents()

    def apply_font_size(self):
        app = QApplication.instance()
        font = app.font()
        font.setPointSize(self.current_font_size)
        app.setFont(font)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VehicleClient()
    window.show()
    sys.exit(app.exec())