from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from ui_adjust_qty import AdjustQtyDialog

# Table columns: (json_key, header_label)
COLUMNS = [
    ("stock_number", "Stock Number"),
    ("noun", "Noun / Nomenclature"),
    ("bin_location", "Bin Location"),
    ("unit_of_issue", "Unit of Issue"),
    ("actual_qty", "Actual Qty"),
    ("authorized_qty", "Authorized Qty"),
    ("unit_price", "Unit Price"),
    ("keywords", "Keywords"),
    ("base_location", "Base"),
]

# Column indexes used by inline filters (based on COLUMNS order above)
IDX_STOCK = 0
IDX_NOUN = 1
IDX_BIN = 2


class InventoryView(QWidget):
    def __init__(self, api, session_state):
        super().__init__()
        self.api = api
        self.s = session_state
        self.items = []

        root = QVBoxLayout()

        # ---- Header ----
        header = QLabel("Inventory")
        header.setStyleSheet("font-size: 18px; font-weight: 800; margin: 6px 0 10px 0;")
        root.addWidget(header)

        # ---- Top Controls: Search + Base + Buttons ----
        controls = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search (stock #, noun, bin, keywords)")
        controls.addWidget(self.search)

        self.base = QLineEdit()
        self.base.setPlaceholderText("Base filter (optional) e.g., Dyess")
        controls.addWidget(self.base)

        self.refresh_btn = QPushButton("Search")
        self.refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(self.refresh_btn)

        self.adjust_btn = QPushButton("Adjust Qty")
        self.adjust_btn.clicked.connect(self.adjust_qty)
        controls.addWidget(self.adjust_btn)

        root.addLayout(controls)

        # Allow pressing Enter in search to refresh
        self.search.returnPressed.connect(self.refresh)
        self.base.returnPressed.connect(self.refresh)

        # ---- Inline Filters (client-side, instant) ----
        filters = QHBoxLayout()

        self.f_stock = QLineEdit()
        self.f_stock.setPlaceholderText("Filter Stock # (instant)")
        filters.addWidget(self.f_stock)

        self.f_noun = QLineEdit()
        self.f_noun.setPlaceholderText("Filter Noun (instant)")
        filters.addWidget(self.f_noun)

        self.f_bin = QLineEdit()
        self.f_bin.setPlaceholderText("Filter Bin (instant)")
        filters.addWidget(self.f_bin)

        root.addLayout(filters)

        self.f_stock.textChanged.connect(self.apply_filters)
        self.f_noun.textChanged.connect(self.apply_filters)
        self.f_bin.textChanged.connect(self.apply_filters)

        # ---- Table ----
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([c[1] for c in COLUMNS])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)  # ✅ Column sorting
        root.addWidget(self.table)

        self.setLayout(root)

        # Permissions + initial state
        self.apply_permissions()

    def apply_permissions(self):
        # Only admin/clerk can adjust qty
        self.adjust_btn.setEnabled(self.s.role in {"admin", "clerk"})

    def refresh(self):
        """Fetch items from backend using server-side search/base filters."""
        try:
            q = self.search.text().strip()
            base = self.base.text().strip()

            self.items = self.api.search_items(q=q, base=base)
            self.populate()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load items.\n\n{e}")

    def populate(self):
        """Populate table with the fetched items."""
        # Turn off sorting while inserting rows to avoid jumpiness
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for it in self.items:
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col_idx, (key, _) in enumerate(COLUMNS):
                val = it.get(key, "")

                # Nice formatting for numbers
                if key in {"actual_qty", "authorized_qty"}:
                    try:
                        val = int(val)
                    except Exception:
                        pass
                if key in {"unit_price"}:
                    try:
                        val = float(val)
                    except Exception:
                        pass

                cell = QTableWidgetItem(str(val))

                # Align numeric columns
                if key in {"actual_qty", "authorized_qty", "unit_price"}:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                self.table.setItem(row, col_idx, cell)

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

        # Apply inline filters after repopulating
        self.apply_filters()

    def apply_filters(self):
        """Client-side filtering that hides rows without refetching."""
        s = self.f_stock.text().strip().lower()
        n = self.f_noun.text().strip().lower()
        b = self.f_bin.text().strip().lower()

        for row in range(self.table.rowCount()):
            stock = self._cell_text(row, IDX_STOCK)
            noun = self._cell_text(row, IDX_NOUN)
            binloc = self._cell_text(row, IDX_BIN)

            show = True
            if s and s not in stock:
                show = False
            if n and n not in noun:
                show = False
            if b and b not in binloc:
                show = False

            self.table.setRowHidden(row, not show)

    def _cell_text(self, row: int, col: int) -> str:
        item = self.table.item(row, col)
        return item.text().lower() if item else ""

    def get_selected(self):
        """Return the selected item dict from self.items based on selected row."""
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return None

        # If sorting/filtering is enabled, the table row order may not match self.items order.
        # We'll read stock_number + base_location from the selected row and look it up.
        row = sel[0].row()
        stock = self.table.item(row, IDX_STOCK).text() if self.table.item(row, IDX_STOCK) else ""
        base = self.table.item(row, 8).text() if self.table.item(row, 8) else ""  # base_location column index

        for it in self.items:
            if str(it.get("stock_number", "")) == stock and str(it.get("base_location", "")) == base:
                return it

        return None

    def adjust_qty(self):
        """Open Adjust Qty dialog (admin/clerk only)."""
        selected = self.get_selected()
        if not selected:
            QMessageBox.information(self, "Select an Item", "Please select an item row first.")
            return

        dlg = AdjustQtyDialog(
            api=self.api,
            session_state=self.s,
            stock_number=selected["stock_number"],
            base_location=selected["base_location"],
            parent=self
        )

        if dlg.exec():
            self.refresh()
