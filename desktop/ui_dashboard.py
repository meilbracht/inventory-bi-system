from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
from PySide6.QtCore import Qt

def card(title: str, value: str) -> QFrame:
    box = QFrame()
    box.setObjectName("DashCard")
    layout = QVBoxLayout()
    t = QLabel(title)
    t.setStyleSheet("color:#9aa4b2; font-weight:700;")
    v = QLabel(value)
    v.setStyleSheet("font-size:24px; font-weight:900;")
    layout.addWidget(t)
    layout.addWidget(v)
    layout.addStretch()
    box.setLayout(layout)
    return box

class DashboardView(QWidget):
    def __init__(self, api, session_state):
        super().__init__()
        self.api = api
        self.s = session_state

        root = QVBoxLayout()

        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 18px; font-weight: 800; margin: 6px 0 10px 0;")
        root.addWidget(header)

        row = QHBoxLayout()
        self.card_total = card("Total Items", "—")
        self.card_low = card("Low Stock Items", "—")
        self.card_recent = card("Recent Transactions (last 24h)", "—")
        row.addWidget(self.card_total)
        row.addWidget(self.card_low)
        row.addWidget(self.card_recent)
        root.addLayout(row)

        self.refresh_btn = QPushButton("Refresh Dashboard")
        self.refresh_btn.clicked.connect(self.refresh)
        root.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        hint = QLabel("Tip: Use Ctrl+K for command search (stock # or noun).")
        hint.setStyleSheet("color:#777; margin-top:6px;")
        root.addWidget(hint)

        root.addStretch()
        self.setLayout(root)

        # optional: refresh immediately
        self.refresh()

    def refresh(self):
        try:
            base = ""  # could later use a global base selector
            items = self.api.search_items(q="", base=base)
            total = len(items)

            low = sum(1 for x in items if int(x.get("actual_qty", 0)) <= int(x.get("authorized_qty", 0)))

            # recent transactions: use backend limit (we'll just show count for now)
            tx = self.api.get_transactions(base=base, stock_number="", limit=200)
            recent = len(tx)

            self.card_total.layout().itemAt(1).widget().setText(str(total))
            self.card_low.layout().itemAt(1).widget().setText(str(low))
            self.card_recent.layout().itemAt(1).widget().setText(str(recent))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not refresh dashboard.\n\n{e}")
