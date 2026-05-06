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


def fetch_purchase_return_list_rows():
    query = _new_query()
    if not query.exec(
        """
        SELECT pr.id, s.name, COALESCE(r.name, '-'), pr.creation_date
        FROM purchase_return pr
        LEFT JOIN supplier s ON pr.supplier = s.id
        LEFT JOIN rep r ON pr.rep = r.id
        ORDER BY pr.id DESC
        """
    ):
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0)),
                "supplier_name": query.value(1) or "Unknown Supplier",
                "rep_name": query.value(2) or "-",
                "creation_date": _format_date(query.value(3)),
            }
        )
    return rows


def fetch_purchase_return_detail(return_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            pr.id,
            pr.creation_date,
            pr.subtotal,
            pr.total,
            pr.received,
            pr.remaining,
            pr.writeoff,
            s.name,
            COALESCE(r.name, '-')
        FROM purchase_return pr
        LEFT JOIN supplier s ON pr.supplier = s.id
        LEFT JOIN rep r ON pr.rep = r.id
        WHERE pr.id = ?
        """
    )
    query.addBindValue(return_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    if not query.next():
        return None

    return {
        "id": int(query.value(0)),
        "creation_date": _format_date(query.value(1)),
        "subtotal": float(query.value(2) or 0.0),
        "total": float(query.value(3) or 0.0),
        "received": float(query.value(4) or 0.0),
        "remaining": float(query.value(5) or 0.0),
        "writeoff": float(query.value(6) or 0.0),
        "supplier_name": query.value(7) or "Unknown Supplier",
        "rep_name": query.value(8) or "-",
    }


def fetch_purchase_return_item_rows(return_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            p.display_name,
            p.brand,
            pri.batch,
            pri.purchased,
            pri.returned,
            pri.rate,
            pri.total
        FROM purchase_return_item pri
        LEFT JOIN product p ON pri.product = p.id
        WHERE pri.purchase_return = ?
        """
    )
    query.addBindValue(return_id)
    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append(
            {
                "name": query.value(0) or "Unknown",
                "brand": query.value(1) or "",
                "batch": query.value(2),
                "purchased": query.value(3),
                "returned": query.value(4),
                "rate": query.value(5),
                "total": query.value(6),
            }
        )
    return rows


def fetch_active_purchase_return_supplier_options():
    query = _new_query()
    if not query.exec("SELECT id, name FROM supplier WHERE status = 'active' ORDER BY name"):
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append({"id": int(query.value(0)), "name": query.value(1) or ""})
    return rows


def fetch_purchase_return_rep_options(supplier_id):
    query = _new_query()
    query.prepare("SELECT id, name FROM rep WHERE supplier_id = ? ORDER BY name")
    query.addBindValue(supplier_id)
    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append({"id": int(query.value(0)), "name": query.value(1) or ""})
    return rows


def fetch_sales_return_list_rows():
    query = _new_query()
    if not query.exec(
        """
        SELECT
            sr.id,
            CASE
                WHEN sr.customer IS NULL OR sr.customer = '' THEN 'Walk-In Customer'
                ELSE COALESCE(c.name, 'Unknown Customer')
            END,
            COALESCE(a.firstname || ' ' || a.lastname, e.name, '-'),
            sr.creation_date
        FROM salesreturn sr
        LEFT JOIN customer c ON sr.customer = c.id
        LEFT JOIN auth a ON sr.salesman = a.id
        LEFT JOIN employee e ON sr.salesman = e.id
        ORDER BY sr.id DESC
        """
    ):
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0)),
                "customer_name": query.value(1) or "Walk-In Customer",
                "salesman_name": query.value(2) or "-",
                "creation_date": _format_date(query.value(3)),
            }
        )
    return rows


def fetch_sales_return_detail(return_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            sr.id,
            sr.salesorder,
            sr.creation_date,
            sr.subtotal,
            sr.roundoff,
            sr.total,
            sr.paid,
            sr.remaining,
            sr.writeoff,
            CASE
                WHEN sr.customer IS NULL OR sr.customer = '' THEN 'Walk-In Customer'
                ELSE COALESCE(c.name, 'Unknown Customer')
            END,
            COALESCE(e.name, a.firstname || ' ' || a.lastname, '-')
        FROM salesreturn sr
        LEFT JOIN customer c ON sr.customer = c.id
        LEFT JOIN employee e ON sr.salesman = e.id
        LEFT JOIN auth a ON sr.salesman = a.id
        WHERE sr.id = ?
        """
    )
    query.addBindValue(return_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    if not query.next():
        return None

    return {
        "id": int(query.value(0)),
        "salesorder_id": query.value(1),
        "creation_date": _format_date(query.value(2)),
        "subtotal": query.value(3),
        "roundoff": query.value(4),
        "total": query.value(5),
        "paid": query.value(6),
        "remaining": query.value(7),
        "writeoff": query.value(8),
        "customer_name": query.value(9) or "Walk-In Customer",
        "salesman_name": query.value(10) or "-",
    }


def fetch_sales_return_item_rows(return_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            p.display_name,
            p.brand,
            s.sold,
            s.returned,
            s.rate,
            s.total
        FROM salesreturn_item s
        LEFT JOIN product p ON s.product = p.id
        WHERE s.salesreturn = ?
        """
    )
    query.addBindValue(return_id)
    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append(
            {
                "name": query.value(0) or "Unknown",
                "brand": query.value(1) or "",
                "sold": query.value(2),
                "returned": query.value(3),
                "rate": query.value(4),
                "total": query.value(5),
            }
        )
    return rows


def fetch_active_sales_return_salesman_options():
    query = _new_query()
    if not query.exec("SELECT id, name FROM employee WHERE status = 'active' ORDER BY name"):
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append({"id": int(query.value(0)), "name": query.value(1) or ""})
    return rows


def fetch_sales_return_salesitem_product_id(salesitem_id):
    query = _new_query()
    query.prepare("SELECT product_id FROM salesitem WHERE id = ?")
    query.addBindValue(salesitem_id)
    if not query.exec() or not query.next():
        raise Exception("Product lookup failed")
    return query.value(0)


def fetch_sales_return_sales_header(sales_id):
    query = _new_query()
    query.prepare(
        """
        SELECT customer, salesman, discount, tax, creation_date
        FROM sales
        WHERE id = ?
        """
    )
    query.addBindValue(sales_id)
    if not query.exec() or not query.next():
        return None
    return {
        "customer": query.value(0),
        "salesman": query.value(1),
        "discount": query.value(2),
        "tax": query.value(3),
        "creation_date": query.value(4),
    }


def fetch_sales_return_customer_label(customer_id):
    if customer_id in (None, ""):
        return "Walk-in Customer"
    query = _new_query()
    query.prepare("SELECT name FROM customer WHERE id = ?")
    query.addBindValue(int(customer_id))
    if query.exec() and query.next():
        customer_name = query.value(0)
        return f"{customer_id} - {customer_name}"
    raise Exception(query.lastError().text() or "Customer lookup failed")


def fetch_sales_return_salesman_label(salesman_id):
    query = _new_query()
    query.prepare("SELECT firstname, lastname FROM auth WHERE id = ?")
    query.addBindValue(int(salesman_id))
    if query.exec() and query.next():
        firstname = query.value(0)
        lastname = query.value(1)
        return f"{salesman_id} - {firstname} {lastname}"
    raise Exception(query.lastError().text() or "Salesman lookup failed")


def fetch_sales_return_product_display(product_id):
    query = _new_query()
    query.prepare("SELECT display_name, brand FROM product WHERE id = ?")
    query.addBindValue(product_id)
    if query.exec() and query.next():
        return str(query.value(0)), str(query.value(1))
    raise Exception(query.lastError().text() or "Product lookup failed")


def fetch_sales_return_source_item_rows(sales_id):
    query = _new_query()
    query.prepare(
        """
        SELECT id, product_id, qty_sold, effective_line_total
        FROM salesitem
        WHERE sales_id = ?
        """
    )
    query.addBindValue(sales_id)
    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append(
            {
                "salesitem_id": int(query.value(0)),
                "product_id": int(query.value(1)),
                "qty_sold": int(query.value(2)),
                "effective_line_total": float(query.value(3) or 0.0),
            }
        )
    return rows
