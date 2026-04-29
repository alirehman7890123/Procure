from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QHBoxLayout, QFrame, QVBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem

import os
from PySide6.QtGui import QPdfWriter, QPainter, QPageSize, QFont, QTextOption, QPen, QColor
from PySide6.QtCore import Qt, QRectF

from medic.utilities.stylus import load_stylesheets
from medic.utilities.file_preview import preview_file
from features.sales.services.sales_detail_service import (
    fetch_sales_detail,
    fetch_sales_detail_items,
    fetch_sales_invoice_context,
)




class SalesDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Receipt Detail", objectName="SectionTitle")
        self.receiptlist = QPushButton("Receipt List", objectName="TopRightButton")
        self.receiptlist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.receiptlist)

        self.layout.addLayout(header_layout)
        

        line = QFrame()
        line.setObjectName("lineSeparator")

        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """)

        self.layout.addWidget(line)
        self.layout.addSpacing(20)
        
        
        labels = ["Receipt Id", "Customer", "Salesman", "Order Date", "Due Date"]
        
        
        self.orderid = QLabel()
        self.customer = QLabel()
        self.salesman = QLabel()
        self.orderdate = QLabel()
        self.duedate = QLabel("No Due Date")
        
        fields = [self.orderid, self.customer, self.salesman, self.orderdate, self.duedate]
        
        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            
        
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.24, 0.12, 0.16, 0.11, 0.10, 0.10, 0.12])
        headers = ["##", "Product", "Qty", "Rate", "Disc (%)", "Disc", "Tax (%)", "Total"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   

        self.table.setMinimumWidth(700)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)

        self.prescription_frame = QFrame()
        self.prescription_frame.setObjectName("sectionCard")
        prescription_layout = QVBoxLayout(self.prescription_frame)
        prescription_layout.setContentsMargins(10, 10, 10, 10)
        prescription_layout.setSpacing(8)

        prescription_title = QLabel("Prescription")
        prescription_title.setStyleSheet("font-weight: 700; color: #223746;")
        prescription_layout.addWidget(prescription_title)

        self.prescription_summary = QLabel("No prescription recorded for this invoice.")
        self.prescription_summary.setWordWrap(True)
        prescription_layout.addWidget(self.prescription_summary)

        self.prescription_attachment_table = QTableWidget()
        self.prescription_attachment_table.setColumnCount(4)
        self.prescription_attachment_table.setHorizontalHeaderLabels(["File", "Type", "Size", "Preview"])
        self.prescription_attachment_table.verticalHeader().setVisible(False)
        self.prescription_attachment_table.horizontalHeader().setStretchLastSection(True)
        self.prescription_attachment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prescription_attachment_table.setSelectionMode(QTableWidget.SingleSelection)
        self.prescription_attachment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.prescription_attachment_table.setVisible(False)
        prescription_layout.addWidget(self.prescription_attachment_table)

        self.layout.addWidget(self.prescription_frame)
        
        self.layout.addStretch()    
        

        
        labels = [
            "Sub Total",
            "Discount",
            "Taxable",
            "Tax",
            "Net Amount",
            "Additional Charges",
            "Grand Total",
            "Received",
            "Remaining",
            "Write-Off",
        ]
        
        self.subtotal = QLabel()
        self.discount = QLabel()
        self.taxable = QLabel()
        self.tax = QLabel()
        self.total = QLabel()
        self.roundoff = QLabel()
        self.finalamount = QLabel()
        self.received = QLabel()
        self.remaining = QLabel()
        self.writeoff = QLabel()
        
        fields = [
            self.subtotal,
            self.discount,
            self.taxable,
            self.tax,
            self.total,
            self.roundoff,
            self.finalamount,
            self.received,
            self.remaining,
            self.writeoff,
        ]
        
        
        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            
            
        
        print_button = QPushButton("Print Invoice", objectName="TopRightButton")
        print_button.clicked.connect(lambda: self.export_pdf('salesinvoice.pdf'))
            
        self.layout.addWidget(print_button)
            
        self.layout.addStretch()
            
        # Load and Apply CSS
        self.setStyleSheet(load_stylesheets())

        
        




    def load_sales_data(self, id):
        
        print("Loading Sales ID:", id)
        detail = fetch_sales_detail(id)
        if not detail:
            print("Sales not found for ID:", id)
            return

        self.orderid.setText(str(detail["sales_id"]))
        self.customer.setText(detail["customer_name"])
        self.salesman.setText(detail["salesman_name"])
        self.orderdate.setText(detail["invoice_date"])
        self.duedate.setText(detail["due_date"])
        self.subtotal.setText(f"{detail['subtotal']:.2f}")
        self.discount.setText(f"{detail['discount']:.2f}")
        self.taxable.setText(f"{detail['taxable']:.2f}")
        self.tax.setText(f"{detail['tax']:.2f}")
        self.total.setText(f"{detail['net_amount']:.2f}")
        self.roundoff.setText(f"{detail['additional_charges']:.2f}")
        self.finalamount.setText(f"{detail['final_total']:.2f}")
        self.received.setText(f"{detail['received']:.2f}")
        self.remaining.setText(f"{detail['remaining']:.2f}")
        self.writeoff.setText(f"{detail['writeoff']:.2f}")

        print("Sales data loaded successfully for ID:", id)
        self.load_items_into_table(id)
        self.load_prescription_section(id)
            
            




    def load_items_into_table(self, sale_id):
        
        self.invoice_id = sale_id
        print("Loading items into table")

        self.table.setRowCount(0)  # Clear existing rows
        rows = fetch_sales_detail_items(sale_id)
        for row_index, item in enumerate(rows):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row_index + 1)))
            self.table.setItem(row_index, 1, QTableWidgetItem(item["product_name"]))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(item["qty"])))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(item["rate"])))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(item["discount_percent"])))
            self.table.setItem(row_index, 5, QTableWidgetItem(str(item["discount_amount"])))
            self.table.setItem(row_index, 6, QTableWidgetItem(str(item["tax_percent"])))
            self.table.setItem(row_index, 7, QTableWidgetItem(str(item["line_total"])))

    def load_prescription_section(self, sale_id):
        context = fetch_sales_invoice_context(sale_id)
        prescription = (context or {}).get("prescription")
        attachments = list((context or {}).get("prescription_attachments") or [])
        self._prescription_attachments = attachments

        if not prescription:
            self.prescription_summary.setText("No prescription recorded for this invoice.")
            self.prescription_attachment_table.setRowCount(0)
            self.prescription_attachment_table.setVisible(False)
            return

        parts = [
            f"Doctor: {prescription['doctor_name']}",
            f"Clinic: {prescription['clinic_name'] or 'Not provided'}",
            f"License: {prescription['doctor_license_no'] or 'Not provided'}",
            f"Date: {prescription['prescription_date'] or 'Not provided'}",
            f"Notes: {prescription['notes'] or 'None'}",
        ]
        self.prescription_summary.setText("\n".join(parts))

        self.prescription_attachment_table.setRowCount(0)
        for row_index, attachment in enumerate(attachments):
            self.prescription_attachment_table.insertRow(row_index)
            self.prescription_attachment_table.setItem(row_index, 0, QTableWidgetItem(attachment["original_filename"]))
            self.prescription_attachment_table.setItem(row_index, 1, QTableWidgetItem(attachment["mime_type"] or "file"))
            self.prescription_attachment_table.setItem(row_index, 2, QTableWidgetItem(self._format_file_size(attachment["file_size"])))
            preview_btn = QPushButton("Preview", objectName="TopRightButton")
            preview_btn.clicked.connect(lambda _, r=row_index: self.open_prescription_attachment_by_row(r))
            self.prescription_attachment_table.setCellWidget(row_index, 3, preview_btn)

        has_attachments = bool(attachments)
        self.prescription_attachment_table.setVisible(has_attachments)

    def _format_file_size(self, size_bytes):
        try:
            size = int(size_bytes or 0)
        except (TypeError, ValueError):
            size = 0
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"

    def open_prescription_attachment_by_row(self, row):
        if row < 0 or row >= len(getattr(self, "_prescription_attachments", [])):
            AppMessageBox.information(self, "Preview Attachment", "No attachment row was selected.")
            return
        attachment = self._prescription_attachments[row]
        path = attachment.get("absolute_path") or ""
        if not path or not os.path.exists(path):
            AppMessageBox.warning(
                self,
                "Preview Attachment",
                (
                    "The attachment file could not be found.\n\n"
                    f"Expected path:\n{path or '(missing path)'}"
                ),
            )
            return

        mime_type = str(attachment.get("mime_type") or "").lower()
        extension = os.path.splitext(path)[1].lower()
        try:
            if mime_type.startswith("image/") or extension in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
                dialog = ImagePreviewDialog(path, self)
                if not dialog.preview_ready:
                    AppMessageBox.warning(
                        self,
                        "Image Preview",
                        (
                            "The image file was found, but the in-app preview could not load it.\n\n"
                            f"File:\n{path}"
                        ),
                    )
                    return
                dialog.exec()
                return
            if (mime_type == "application/pdf" or extension == ".pdf") and HAS_QT_PDF:
                dialog = PdfPreviewDialog(path, self)
                if not dialog.preview_ready:
                    AppMessageBox.warning(
                        self,
                        "PDF Preview",
                        (
                            "The PDF file was found, but the in-app PDF viewer could not render it.\n\n"
                            f"File:\n{path}"
                        ),
                    )
                    return
                dialog.exec()
                return
            self._open_attachment_externally(path, mime_type=mime_type, extension=extension)
        except Exception as exc:
            AppMessageBox.critical(
                self,
                "Preview Attachment",
                (
                    "The attachment could not be opened.\n\n"
                    f"File:\n{path}\n\n"
                    f"Reason:\n{exc}"
                ),
            )

    def _open_attachment_externally(self, path, *, mime_type="", extension=""):
        if platform.system() == "Windows":
            os.startfile(path)
            AppMessageBox.information(
                self,
                "Open Attachment",
                (
                    "Opened the attachment with the default system app.\n\n"
                    f"File:\n{path}"
                ),
            )
            return

        command = ["open", path] if platform.system() == "Darwin" else ["xdg-open", path]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            reason = (result.stderr or result.stdout or "Unknown error").strip()
            raise Exception(reason)

        fallback_reason = []
        if extension == ".pdf" and not HAS_QT_PDF:
            fallback_reason.append("QtPdf is not available")
        if mime_type and not mime_type.startswith("image/") and extension != ".pdf":
            fallback_reason.append(f"unsupported preview type: {mime_type or extension}")

        detail = "\n".join(fallback_reason)
        message = "Opened the attachment with the default system app."
        if detail:
            message += f"\n\nPreview fallback reason:\n{detail}"
        message += f"\n\nFile:\n{path}"
        AppMessageBox.information(self, "Open Attachment", message)
            
        
        
        



    
    def export_pdf(self, filename="salesinvoice.pdf"):
        
        
        sales_id = self.invoice_id
        print("Exporting PDF")
        
        print("Sales id is: ", sales_id)
        context = fetch_sales_invoice_context(sales_id)
        if not context:
            print("Sales invoice context not found for ID:", sales_id)
            return

        header = context["header"]
        business = context["business"]
        subtotal = header["subtotal"]
        salesdiscount = header["discount"]
        salestax = header["tax"]
        totalaftertax = header["net_amount"]
        roundoff = header["additional_charges"]
        finaltotal = header["final_total"]
        customer = header["customer_name"]
        salesman = header["salesman_name"]
        invoicedate = header["invoice_date"]
        items = [
            (
                item["product_name"],
                item["qty"],
                item["rate"],
                item["discount_percent"],
                item["rate"] - item["discount_amount"],
                item["line_total"],
            )
            for item in context["items"]
        ]
        business_name = business["business_name"]
        business_address = business["business_address"]
        business_contact = business["business_contact"]

        pdf = QPdfWriter(filename)
        pdf.setPageSize(QPageSize(QPageSize.A4))
        pdf.setResolution(300)

        

        painter = QPainter(pdf)
        painter.setFont(QFont("Arial", 12))
        painter.setPen(Qt.black)
        
        
        
        x = 100
        y = 200

        business_font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(business_font)

        # business name
        painter.drawText(x, y, business_name)

        y += 80
        
        address_font = QFont("Arial", 12)
        painter.setFont(address_font)
        
        address = business_address
        painter.drawText(x, y, address)
        
        y += 70
        contact = business_contact
        painter.drawText(x, y, contact)
        
        
        invoice_font = QFont("Arial", 36, QFont.Bold)
        painter.setFont(invoice_font)

        invoice_title = "Invoice"
        painter.drawText(1700, 230, invoice_title)
        
        invoice_no_font = QFont("Arial", 12)
        painter.setFont(invoice_no_font)
        
        rect = QRectF(1700, 250, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, f"# {sales_id}", option)
        
        
        invoice_date_font = QFont("Arial", 12)
        painter.setFont(invoice_date_font)

        rect = QRectF(1700, 320, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, invoicedate, option)

        y += 150
        
        customer_font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(customer_font)
        painter.drawText(x, y, f"To: {customer}")
        
        y += 80
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)
        
        y += 70
        header_font = QFont("Arial", 11, QFont.Bold)
        painter.setFont(header_font)

        item_name = "Item"
        painter.drawText(x + 20, y, item_name)
        
        item_name = "qty"
        painter.drawText(x + 900, y, item_name)
        
        item_name = "rate"
        painter.drawText(x + 1100, y, item_name)
        
        item_name = "discount"
        painter.drawText(x + 1400, y, item_name)
        
        item_name = "Price"
        painter.drawText(x + 1650, y, item_name)
        
        item_name = "Total"
        painter.drawText(x + 1900, y, item_name)

        
        y += 40
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)

        y += 100
        
        items_font = QFont("Arial", 11)
        painter.setFont(items_font)
        
        # Sample items
        # items = [
        #         ("Panadol tab 250mg", 2, 10.00, "2%", 9.80, 18.16), 
        #         ("Amoxil Cap 500mg", 1, 20.00, "0%", 20.00, 20.00), 
        #         ("Floxacin Drops 10ml", 5, 5.00, "5%", 4.75, 23.75),
        #         ("Clementrin Syrup 160ml", 3, 15.00, "10%", 13.50, 40.50),
        #         ("Tibe Cream 75gm", 4, 12.00, "5%", 11.40, 45.60)
        #     ]
        
        print("Drawing Items into Table")
        
        for item, qty, rate, discount, net_price, item_total in items:

            painter.drawText(x + 20, y, item)
            painter.drawText(x + 900, y, str(qty))
            painter.drawText(x + 1100, y, f"{rate:.2f}")
            painter.drawText(x + 1400, y, f"{discount:.1f} %")
            painter.drawText(x + 1650, y, f"{net_price:.2f}")
            painter.drawText(x + 1900, y, f"{item_total:.2f}")
            
            y += 80

        y += 40
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)
        
        y += 60
        
        rect = QRectF(1500, y, 400, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, "Sub Total", option)
        
        total_font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(total_font)
        rect = QRectF(1950, y, 200, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, f"{subtotal}", option)
        
        
        y += 100
        painter.drawText(x + 1600, y, f"Discount: ")
        painter.drawText(x + 1900, y, f"{salesdiscount}")
        
        y += 80
        painter.drawText(x + 1600, y, f"Sales Tax: ")
        painter.drawText(x + 1900, y, f"{salestax:.2f}")
        
        y += 80
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x + 1500, y, pdf.width() - 200, y) 
        
        y += 80
        total_font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(total_font)
        painter.drawText(x + 1500, y, f"Total Amount: ")
        painter.drawText(x + 1950, y, f"{finaltotal:.2f}")

        painter.end()
        
        self.print_pdf(filename)
        
        
    

    def print_pdf(self, filename):
        
        system = platform.system()
        if system in ("Linux", "Darwin"):
            os.system(f"lp '{filename}'")
        elif system == "Windows":
            os.startfile(filename, "print")

                
            



class MyTable(QTableWidget):
    
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)


            
        
