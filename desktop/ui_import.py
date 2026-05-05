from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt


class ImportInventoryView(QWidget):
    def __init__(self, api, session_state):
        super().__init__()
        self.api = api
        self.s = session_state

        root = QVBoxLayout()

        header = QLabel("Admin • Import Inventory (Excel)")
        header.setStyleSheet("font-size: 18px; font-weight: 800; margin: 6px 0 10px 0;")
        root.addWidget(header)

        info = QLabel(
            "Upload an Excel (.xlsx) file to import inventory items.\n"
            "Required columns:\n"
            "Stock Number, Noun / Nomenclature, Bin Location, Unit of Issue,\n"
            "Actual Qty, Authorized Qty, Unit Price, Keywords, Base"
        )
        info.setStyleSheet("color:#9aa4b2;")
        root.addWidget(info)

        self.btn_import = QPushButton("Select Excel File & Import")
        self.btn_import.setMinimumHeight(42)
        self.btn_import.clicked.connect(self.import_excel)
        root.addWidget(self.btn_import, alignment=Qt.AlignmentFlag.AlignLeft)

        root.addStretch()
        self.setLayout(root)

    def import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            result = self.api.import_items(self.s.username, self.s.role, path)
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {result.get('imported', 0)} items."
            )
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))
