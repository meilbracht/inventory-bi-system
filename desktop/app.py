import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from api_client import ApiClient
from state import SessionState
from ui_login import LoginView
from ui_main import MainWindow

def main():
    app = QApplication(sys.argv)

    app.setStyleSheet("""
QWidget {
    background: #0f1115;
    color: #e8eaed;
    font-size: 12px;
}

QLineEdit, QComboBox, QSpinBox {
    background: #151823;
    border: 1px solid #2a2f3a;
    border-radius: 10px;
    padding: 8px;
    color: #e8eaed;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #4c8dff;
}

QPushButton {
    background: #1b2030;
    border: 1px solid #2a2f3a;
    border-radius: 12px;
    padding: 9px 12px;
    font-weight: 600;
}
QPushButton:hover { background: #232a3d; }
QPushButton:pressed { background: #141a28; }
QPushButton:disabled {
    background: #141721;
    color: #7b8190;
    border: 1px solid #23283a;
}

QTableWidget {
    background: #0f1115;
    alternate-background-color: #121522;
    border: 1px solid #2a2f3a;
    border-radius: 12px;
    gridline-color: #2a2f3a;
}
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected {
    background: #1d2a44;
    color: #e8eaed;
}
QHeaderView::section {
    background: #151823;
    color: #e8eaed;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #2a2f3a;
    font-weight: 700;
}

QMessageBox {
    background: #0f1115;
}

QScrollBar:vertical {
    background: #0f1115;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #2a2f3a;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #3a4253; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
""")
    
    session = SessionState()
    api = ApiClient(session.base_url)

    stack = QStackedWidget()
    login = LoginView(api)
    stack.addWidget(login)
    stack.setWindowTitle("USAF Inventory & BI")
    stack.resize(500, 250)

    def on_login(username, role):
        session.username = username
        session.role = role
        main_win = MainWindow(api, session)
        stack.addWidget(main_win)
        stack.setCurrentWidget(main_win)

    login.logged_in.connect(on_login)
    stack.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
