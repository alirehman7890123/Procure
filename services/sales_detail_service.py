from PySide6.QtCore import QDate, QDateTime
from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def _format_date(value):
    if isinstance(value, QDateTime):
        return value.date().toString("dd-MM-yyyy")
    if isinstance(value, QDate):
        return value.toString("dd-MM-yyyy")
    return str(value or "")


def fetch_sales_detail(sales_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            s.id,
            s.customer,
            COALESCE(c.name, 'Walk-in Customer'),
            s.salesman,
            TRIM(COALESCE(a.firstname, '') || ' ' || COALESCE(a.lastname, '')),
            s.creation_date,
            s.subtotal,
            s.discount,
            s.taxable,
            s.tax,
            s.net_amount,
            s.additional_charges,
            s.total,
            s.received,
            s.remaining,
            s.writeoff,
            s.due_date
        FROM sales s
        LEFT JOIN customer c ON c.id = s.customer
        LEFT JOIN auth a ON a.id = s.salesman
        WHERE s.id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(sales_id))

    if not query.exec():
        raise Exception(f"Failed to load sales detail: {query.lastError().text()}")
    if not query.next():
        return None

    salesman_name = str(query.value(4) or "").strip() or "-"

    return {
        "sales_id": int(query.value(0) or 0),
        "customer_id": query.value(1),
        "customer_name": str(query.value(2) or "Walk-in Customer").strip() or "Walk-in Customer",
        "salesman_id": int(query.value(3) or 0),
        "salesman_name": salesman_name,
        "invoice_date": _format_date(query.value(5)),
        "subtotal": float(query.value(6) or 0.0),
        "discount": float(query.value(7) or 0.0),
        "taxable": float(query.value(8) or 0.0),
        "tax": float(query.value(9) or 0.0),
        "net_amount": float(query.value(10) or 0.0),
        "additional_charges": float(query.value(11) or 0.0),
        "final_total": float(query.value(12) or 0.0),
        "received": float(query.value(13) or 0.0),
        "remaining": float(query.value(14) or 0.0),
        "writeoff": float(query.value(15) or 0.0),
        "due_date": str(query.value(16) or "").strip() or "No Due Date",
    }


def fetch_sales_detail_items(sales_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            si.product_id,
            COALESCE(p.display_name, ''),
            si.qty_sold,
            si.unit_price,
            si.discount,
            si.discount_amount,
            si.tax,
            si.line_total
        FROM salesitem si
        LEFT JOIN product p ON p.id = si.product_id
        WHERE si.sales_id = ?
        ORDER BY si.id ASC
        """
    )
    query.addBindValue(int(sales_id))

    if not query.exec():
        raise Exception(f"Failed to load sales detail items: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or "").strip(),
                "qty": float(query.value(2) or 0.0),
                "rate": float(query.value(3) or 0.0),
                "discount_percent": float(query.value(4) or 0.0),
                "discount_amount": float(query.value(5) or 0.0),
                "tax_percent": float(query.value(6) or 0.0),
                "line_total": float(query.value(7) or 0.0),
            }
        )
    return rows


def fetch_business_identity():
    query = _new_query()
    query.prepare("SELECT businessname, address, contact FROM business WHERE id = 1 LIMIT 1")

    if not query.exec():
        raise Exception(f"Failed to load business identity: {query.lastError().text()}")
    if not query.next():
        return {
            "business_name": "",
            "business_address": "",
            "business_contact": "",
        }

    return {
        "business_name": str(query.value(0) or "").strip(),
        "business_address": str(query.value(1) or "").strip(),
        "business_contact": str(query.value(2) or "").strip(),
    }


def fetch_sales_invoice_context(sales_id):
    header = fetch_sales_detail(sales_id)
    if not header:
        return None
    return {
        "header": header,
        "items": fetch_sales_detail_items(sales_id),
        "business": fetch_business_identity(),
    }
