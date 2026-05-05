from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
from PySide6.QtCore import Signal

class LoginView(QWidget):
    logged_in = Signal(str, str)  # username, role

    def __init__(self, api):
        super().__init__()
        self.api = api

        layout = QVBoxLayout()

        title = QLabel("USAF Inventory & BI")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Login to continue")
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)

        btn_row = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.do_login)
        btn_row.addWidget(self.login_btn)

        layout.addLayout(btn_row)
        self.setLayout(layout)

    def do_login(self):
        u = self.username.text().strip()
        p = self.password.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Missing Info", "Please enter username and password.")
            return
        try:
            data = self.api.login(u, p)
            self.logged_in.emit(data["username"], data["role"])
        except Exception as e:
            QMessageBox.critical(self, "Login Failed", f"Could not login.\n\n{e}")
