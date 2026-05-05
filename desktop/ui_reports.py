from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime


def draw_header(c, title: str, subtitle: str):
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 760, title)
    c.setFont("Helvetica", 10)
    c.drawString(50, 744, subtitle)
    c.line(50, 735, 560, 735)


def draw_footer(c, page_num: int):
    c.setFont("Helvetica", 9)
    c.line(50, 40, 560, 40)
    c.drawString(50, 28, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawRightString(560, 28, f"Page {page_num}")


class ReportsView(QWidget):
    def __init__(self, api, session_state):
        super().__init__()
        self.api = api
        self.s = session_state

        root = QVBoxLayout()

        header = QLabel("Reports")
        header.setStyleSheet("font-size: 18px; font-weight: 800; margin: 6px 0 10px 0;")
        root.addWidget(header)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.base = QLineEdit()
        self.base.setPlaceholderText("Base filter (optional) e.g., Dyess")
        self.base.setMinimumHeight(36)
        controls.addWidget(self.base)

        self.stock = QLineEdit()
        self.stock.setPlaceholderText("Stock Number filter (optional)")
        self.stock.setMinimumHeight(36)
        controls.addWidget(self.stock)

        self.report_type = QComboBox()
        self.report_type.setMinimumHeight(36)
        self.report_type.addItems(["Low Stock", "Inventory Valuation", "Transaction History"])
        controls.addWidget(self.report_type)

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setMinimumHeight(36)
        self.export_csv_btn.clicked.connect(self.export_csv)
        controls.addWidget(self.export_csv_btn)

        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.setMinimumHeight(36)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        controls.addWidget(self.export_pdf_btn)

        root.addLayout(controls)

        hint = QLabel("Tip: Use Base + Stock filters to generate per-base or per-item reports (helps the 2-location requirement).")
        hint.setStyleSheet("color:#777; margin-top:4px;")
        root.addWidget(hint)

        root.addStretch()
        self.setLayout(root)

    # -------------------------
    # Data selection per report
    # -------------------------
    def _get_report_rows(self):
        base = self.base.text().strip()
        stock = self.stock.text().strip()
        report = self.report_type.currentText()

        # Transaction History uses the transactions endpoint
        if report == "Transaction History":
            rows = self.api.get_transactions(base=base, stock_number=stock, limit=500)
            return rows, report, base, stock

        # Inventory-based reports use items endpoint
        items = self.api.search_items(q=stock, base=base) if stock else self.api.search_items(q="", base=base)

        if report == "Low Stock":
            rows = [x for x in items if int(x.get("actual_qty", 0)) <= int(x.get("authorized_qty", 0))]
            return rows, report, base, stock

        # Inventory Valuation
        rows = items
        for x in rows:
            x["extended_value"] = float(x.get("unit_price", 0.0)) * int(x.get("actual_qty", 0))
        return rows, report, base, stock

    # -------------------------
    # CSV export
    # -------------------------
    def export_csv(self):
        try:
            rows, report, base, stock = self._get_report_rows()
            if not rows:
                QMessageBox.information(self, "No Data", "No rows matched this report.")
                return

            default_name = f"{report.replace(' ', '_')}_{base or 'ALL'}_{stock or 'ALL'}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            path, _ = QFileDialog.getSaveFileName(self, "Save CSV", default_name, "CSV Files (*.csv)")
            if not path:
                return

            df = pd.DataFrame(rows)
            df.to_csv(path, index=False)
            QMessageBox.information(self, "Saved", f"CSV exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not export CSV.\n\n{e}")

    # -------------------------
    # PDF export (pro formatting)
    # -------------------------
    def export_pdf(self):
        try:
            rows, report, base, stock = self._get_report_rows()
            if not rows:
                QMessageBox.information(self, "No Data", "No rows matched this report.")
                return

            default_name = f"{report.replace(' ', '_')}_{base or 'ALL'}_{stock or 'ALL'}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            path, _ = QFileDialog.getSaveFileName(self, "Save PDF", default_name, "PDF Files (*.pdf)")
            if not path:
                return

            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter

            subtitle = f"Base: {base or 'ALL'}  •  Stock: {stock or 'ALL'}"
            title = f"{report} Report"

            # Choose columns per report
            if report == "Transaction History":
                cols = ["created_at", "stock_number", "base_location", "username", "action",
                        "qty_change", "qty_before", "qty_after", "reason"]
            elif report == "Inventory Valuation":
                cols = ["stock_number", "noun", "bin_location", "unit_of_issue",
                        "actual_qty", "authorized_qty", "unit_price", "extended_value"]
            else:  # Low Stock
                cols = ["stock_number", "noun", "bin_location", "unit_of_issue",
                        "actual_qty", "authorized_qty", "unit_price"]

            # Pagination setup
            page = 1
            draw_header(c, title, subtitle)
            draw_footer(c, page)

            y = 710
            line_height = 12

            # Column header row
            c.setFont("Helvetica-Bold", 9)
            header_line = " | ".join(cols)
            c.drawString(50, y, header_line[:120])
            y -= line_height
            c.setFont("Helvetica", 9)

            # Rows
            max_rows = 800  # safety limit
            for i, r in enumerate(rows[:max_rows]):
                # Build a single line. Keep it readable and clipped.
                def fmt(v):
                    if v is None:
                        return ""
                    return str(v)

                line = " | ".join(fmt(r.get(k, "")) for k in cols)
                c.drawString(50, y, line[:120])
                y -= line_height

                if y < 60:
                    c.showPage()
                    page += 1
                    draw_header(c, title, subtitle)
                    draw_footer(c, page)
                    y = 710

                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(50, y, header_line[:120])
                    y -= line_height
                    c.setFont("Helvetica", 9)

            c.save()
            QMessageBox.information(self, "Saved", f"PDF exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not export PDF.\n\n{e}")
