from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from ui_dashboard import DashboardView
from ui_inventory import InventoryView
from ui_reports import ReportsView
from ui_admin_users import AdminUsersView
from ui_import import ImportInventoryView


class MainWindow(QWidget):
    def __init__(self, api, session_state):
        super().__init__()
        self.api = api
        self.s = session_state

        self.setWindowTitle("USAF Inventory & BI")
        self.resize(1200, 700)

        # ---- Root layout (Sidebar + Right Area) ----
        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # =========================
        # Sidebar
        # =========================
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFixedWidth(250)
        sidebar_widget.setStyleSheet("""
            QWidget { background: #0b0d12; }
            QLabel { background: transparent; }
            QPushButton {
                text-align: left;
                padding: 10px 12px;
                border: 1px solid transparent;
                border-radius: 12px;
                background: transparent;
                color: #e8eaed;
                font-weight: 600;
            }
            QPushButton:hover { background: #141a28; }
            QPushButton:pressed { background: #101521; }
        """)

        title = QLabel("USAF Inventory")
        title.setStyleSheet("font-size: 16px; font-weight: 900; padding: 6px 4px;")
        sidebar_layout.addWidget(title)

        self.user_label = QLabel(f"User: {self.s.username}\nRole: {self.s.role}")
        self.user_label.setStyleSheet("color:#9aa4b2; padding: 0 4px 8px 4px;")
        sidebar_layout.addWidget(self.user_label)

        # ---- Nav buttons ----
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_inventory = QPushButton("Inventory")
        self.btn_reports = QPushButton("Reports")

        # Admin (two full pages)
        self.btn_admin_users = QPushButton("Admin • Users & Roles")
        self.btn_admin_import = QPushButton("Admin • Import Inventory")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_inventory)
        sidebar_layout.addWidget(self.btn_reports)

        # A small divider label for admin section (optional)
        self.admin_label = QLabel("Admin")
        self.admin_label.setStyleSheet("color:#7f8796; font-weight:800; padding: 8px 4px 0 4px;")
        sidebar_layout.addWidget(self.admin_label)

        sidebar_layout.addWidget(self.btn_admin_users)
        sidebar_layout.addWidget(self.btn_admin_import)

        sidebar_layout.addStretch()

        # =========================
        # Pages (Stacked)
        # =========================
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("QStackedWidget { background: #0f1115; border: none; }")

        self.page_dashboard = DashboardView(self.api, self.s)          # index 0
        self.page_inventory = InventoryView(self.api, self.s)          # index 1
        self.page_reports = ReportsView(self.api, self.s)              # index 2
        self.page_admin_users = AdminUsersView(self.api, self.s)       # index 3
        self.page_admin_import = ImportInventoryView(self.api, self.s) # index 4

        self.pages.addWidget(self.page_dashboard)
        self.pages.addWidget(self.page_inventory)
        self.pages.addWidget(self.page_reports)
        self.pages.addWidget(self.page_admin_users)
        self.pages.addWidget(self.page_admin_import)

        # =========================
        # Right side (Top bar + pages)
        # =========================
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(16, 14, 16, 16)
        right_layout.setSpacing(12)

        # Top bar search (Ctrl+K)
        topbar = QHBoxLayout()
        topbar.setSpacing(10)

        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Search stock number / noun (Ctrl+K)")
        self.global_search.setMinimumHeight(36)
        topbar.addWidget(self.global_search, 1)

        self.btn_go_search = QPushButton("Search")
        self.btn_go_search.setMinimumHeight(36)
        topbar.addWidget(self.btn_go_search)

        right_layout.addLayout(topbar)
        right_layout.addWidget(self.pages, 1)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Add to root
        root.addWidget(sidebar_widget)
        root.addWidget(right_widget, 1)
        self.setLayout(root)

        # =========================
        # Wire navigation
        # =========================
        self.btn_dashboard.clicked.connect(lambda: self.navigate(0, self.btn_dashboard))
        self.btn_inventory.clicked.connect(lambda: self.navigate(1, self.btn_inventory))
        self.btn_reports.clicked.connect(lambda: self.navigate(2, self.btn_reports))
        self.btn_admin_users.clicked.connect(lambda: self.navigate(3, self.btn_admin_users))
        self.btn_admin_import.clicked.connect(lambda: self.navigate(4, self.btn_admin_import))

        # =========================
        # Global search behavior
        # =========================
        self.btn_go_search.clicked.connect(self.run_global_search)
        self.global_search.returnPressed.connect(self.run_global_search)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=lambda: self.global_search.setFocus())

        # Permissions + initial state
        self.apply_permissions()

        # Start on dashboard
        self.pages.setCurrentIndex(0)
        self.set_active_nav(self.btn_dashboard)

    def apply_permissions(self):
        is_admin = (self.s.role == "admin")

        # Only show admin section if admin
        self.admin_label.setVisible(is_admin)
        self.btn_admin_users.setVisible(is_admin)
        self.btn_admin_import.setVisible(is_admin)

        # If not admin and currently on admin pages, force to dashboard
        if not is_admin and self.pages.currentIndex() in {3, 4}:
            self.pages.setCurrentIndex(0)
            self.set_active_nav(self.btn_dashboard)

    def navigate(self, index: int, btn: QPushButton):
        # Prevent non-admin navigation to admin pages
        if index in {3, 4} and self.s.role != "admin":
            return

        self.pages.setCurrentIndex(index)
        self.set_active_nav(btn)

        # Optional: auto-refresh some pages when opened
        if index == 0:  # dashboard
            try:
                self.page_dashboard.refresh()
            except Exception:
                pass
        elif index == 3:  # admin users
            try:
                self.page_admin_users.refresh()
            except Exception:
                pass

    def set_active_nav(self, active_btn: QPushButton):
        buttons = [
            self.btn_dashboard,
            self.btn_inventory,
            self.btn_reports,
            self.btn_admin_users,
            self.btn_admin_import
        ]

        for b in buttons:
            if not b.isVisible():
                continue
            b.setStyleSheet("")  # reset to sidebar defaults

        active_btn.setStyleSheet("""
            QPushButton {
                background: #151823;
                border: 1px solid #2a2f3a;
            }
        """)

    def run_global_search(self):
        text = self.global_search.text().strip()

        # Navigate to Inventory
        self.pages.setCurrentIndex(1)
        self.set_active_nav(self.btn_inventory)

        # Push search into InventoryView and refresh
        self.page_inventory.search.setText(text)
        self.page_inventory.refresh()
