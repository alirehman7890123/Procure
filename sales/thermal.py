from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument

class ReceiptPrinter:
    def __init__(self, parent=None):
        self.parent = parent

    def build_receipt_html(self, shop_name, customer, items, total):
        # items is a list of tuples: [(name, qty, price), ...]
        rows = ""
        for name, qty, price in items:
            rows += f"<tr><td>{name}</td><td align='right'>{qty} x {price}</td></tr>"

        html = f"""
        <div style="width:250px; font-family: Courier New; font-size:10pt;">
            <h2 style="text-align:center; margin:0;">{shop_name}</h2>
            <hr>
            <p>Date: 2025-09-30<br>Customer: {customer}</p>
            <table width="100%" style="border-collapse:collapse;">
                {rows}
            </table>
            <hr>
            <p style="text-align:right; font-weight:bold;">Total: {total}</p>
            <p style="text-align:center;">Thank you for shopping!</p>
        </div>
        """
        return html

    def print_receipt(self, html):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self.parent)

        if dialog.exec() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(printer)
