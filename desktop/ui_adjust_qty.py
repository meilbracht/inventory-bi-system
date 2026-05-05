from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QSpinBox, QLineEdit, QPushButton, QMessageBox, QHBoxLayout

class AdjustQtyDialog(QDialog):
    def __init__(self, api, session_state, stock_number: str, base_location: str, parent=None):
        super().__init__(parent)
        self.api = api
        self.s = session_state
        self.stock_number = stock_number
        self.base_location = base_location

        self.setWindowTitle("Adjust Quantity")
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Stock Number: {stock_number}"))
        layout.addWidget(QLabel(f"Base: {base_location}"))

        self.action = QComboBox()
        self.action.addItems(["add", "subtract"])
        layout.addWidget(QLabel("Action"))
        layout.addWidget(self.action)

        self.qty = QSpinBox()
        self.qty.setRange(1, 1_000_000)
        self.qty.setValue(1)
        layout.addWidget(QLabel("Quantity"))
        layout.addWidget(self.qty)

        self.reason = QLineEdit()
        self.reason.setPlaceholderText("Reason (required) e.g., Receipt / Issue / Adjustment")
        layout.addWidget(QLabel("Reason"))
        layout.addWidget(self.reason)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("Submit")
        self.ok_btn.clicked.connect(self.submit)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.setLayout(layout)

    def submit(self):
        reason = self.reason.text().strip()
        if not reason:
            QMessageBox.warning(self, "Missing Reason", "Please enter a reason for this adjustment.")
            return
        try:
            self.api.adjust_qty(
            username=self.s.username,
            role=self.s.role,
            stock_number=self.stock_number,
            base_location=self.base_location,
            action=self.action.currentText(),
            qty=int(self.qty.value()),
            reason=reason,
)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Failed", f"Could not adjust quantity.\n\n{e}")
