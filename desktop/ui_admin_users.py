from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt

class AdminUsersView(QWidget):
    def __init__(self, api, session_state):
        super().__init__()
        self.api = api
        self.s = session_state
        self.users = []

        root = QVBoxLayout()

        header = QLabel("Admin • Users & Roles")
        header.setStyleSheet("font-size: 18px; font-weight: 800; margin: 6px 0 10px 0;")
        root.addWidget(header)

        # Create user row
        create_row = QHBoxLayout()
        self.new_user = QLineEdit()
        self.new_user.setPlaceholderText("New username")
        create_row.addWidget(self.new_user)

        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("Temporary password")
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        create_row.addWidget(self.new_pass)

        self.new_role = QComboBox()
        self.new_role.addItems(["viewer", "clerk", "admin"])
        create_row.addWidget(self.new_role)

        self.btn_add = QPushButton("Create User")
        self.btn_add.clicked.connect(self.create_user)
        create_row.addWidget(self.btn_add)

        self.btn_import = QPushButton("Import Inventory (Excel)")
        self.btn_import.clicked.connect(self.open_import)
        root.addWidget(self.btn_import)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        create_row.addWidget(self.btn_refresh)

        root.addLayout(create_row)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Active"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        # Actions row
        actions = QHBoxLayout()

        self.role_change = QComboBox()
        self.role_change.addItems(["viewer", "clerk", "admin"])
        actions.addWidget(QLabel("Set selected role:"))
        actions.addWidget(self.role_change)

        self.btn_set_role = QPushButton("Update Role")
        self.btn_set_role.clicked.connect(self.update_role)
        actions.addWidget(self.btn_set_role)

        self.btn_delete = QPushButton("Disable/Delete User")
        self.btn_delete.clicked.connect(self.delete_user)
        actions.addWidget(self.btn_delete)

        actions.addStretch()
        root.addLayout(actions)

        self.setLayout(root)

        # Load initial
        self.refresh()

    def refresh(self):
        try:
            self.users = self.api.list_users(self.s.username, self.s.role)
            self.populate()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load users.\n\n{e}")

    def populate(self):
        self.table.setRowCount(0)
        for u in self.users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(u.get("id"))))
            self.table.setItem(row, 1, QTableWidgetItem(u.get("username", "")))
            self.table.setItem(row, 2, QTableWidgetItem(u.get("role", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(u.get("is_active", True))))

        self.table.resizeColumnsToContents()

    def get_selected_user(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return None
        row = sel[0].row()
        return self.users[row]

    def create_user(self):
        u = self.new_user.text().strip()
        p = self.new_pass.text().strip()
        r = self.new_role.currentText()

        if not u or not p:
            QMessageBox.warning(self, "Missing Info", "Enter username and temporary password.")
            return

        try:
            self.api.create_user(self.s.username, self.s.role, u, p, r)
            self.new_user.setText("")
            self.new_pass.setText("")
            self.refresh()
            QMessageBox.information(self, "Success", "User created.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create user.\n\n{e}")

    def update_role(self):
        selected = self.get_selected_user()
        if not selected:
            QMessageBox.information(self, "Select a user", "Select a user row first.")
            return

        new_role = self.role_change.currentText()
        try:
            self.api.update_user_role(self.s.username, self.s.role, int(selected["id"]), new_role)
            self.refresh()
            QMessageBox.information(self, "Success", "Role updated.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not update role.\n\n{e}")

    def delete_user(self):
        selected = self.get_selected_user()
        if not selected:
            QMessageBox.information(self, "Select a user", "Select a user row first.")
            return

        if selected.get("username") == self.s.username:
            QMessageBox.warning(self, "Not allowed", "You cannot disable/delete your own account while logged in.")
            return

        try:
            self.api.delete_user(self.s.username, self.s.role, int(selected["id"]))
            self.refresh()
            QMessageBox.information(self, "Done", "User disabled/deleted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not disable/delete user.\n\n{e}")
    
    def open_import(self):
        from ui_import import ImportInventoryView
        dlg = ImportInventoryView(self.api, self.s)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.resize(600, 300)
        dlg.show()
