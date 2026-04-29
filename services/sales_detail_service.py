from PySide6.QtCore import QDate, QDateTime
from PySide6.QtSql import QSqlQuery
try:
    from medic.services.accounting_settings_service import load_sales_policy_settings
    from medic.services.sales_transaction_service import (
        ensure_prescription_schema,
        fetch_sales_prescription_attachments,
        fetch_sales_prescription_by_sales_id,
    )
except ModuleNotFoundError:
    from services.accounting_settings_service import load_sales_policy_settings
    from services.sales_transaction_service import (
        ensure_prescription_schema,
        fetch_sales_prescription_attachments,
        fetch_sales_prescription_by_sales_id,
    )


def _new_query():
    return QSqlQuery()


def _format_date(value):
    if isinstance(value, QDateTime):
        return value.date().toString("dd-MM-yyyy")
    if isinstance(value, QDate):
        return value.toString("dd-MM-yyyy")
    return str(value or "")


def fetch_sales_receipt_list_rows(date_from, date_to, search_text="", barcode_code=None):
    query = _new_query()
    search_text = str(search_text or "").strip()
    pattern = f"%{search_text}%"
    from_date = f"{date_from} 00:00:00"
    to_date = f"{date_to} 23:59:59"

    if barcode_code:
        query.prepare(
            """
            SELECT
                s.id,
                COALESCE(c.name, 'Walk-in Customer'),
                (
                    SELECT GROUP_CONCAT(pr.display_name, ' | ')
                    FROM salesitem si
                    LEFT JOIN product pr ON pr.id = si.product_id
                    WHERE si.sales_id = s.id
                ) AS products,
                s.received,
                s.creation_date
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            WHERE s.creation_date BETWEEN ? AND ?
              AND EXISTS (
                  SELECT 1
                  FROM salesitem si2
                  JOIN product p2 ON p2.id = si2.product_id
                  WHERE si2.sales_id = s.id
                    AND TRIM(CAST(p2.code AS TEXT)) = ?
              )
            ORDER BY s.id DESC
            """
        )
        query.addBindValue(from_date)
        query.addBindValue(to_date)
        query.addBindValue(str(barcode_code).strip())
    else:
        query.prepare(
            """
            SELECT
                s.id,
                COALESCE(c.name, 'Walk-in Customer'),
                (
                    SELECT GROUP_CONCAT(pr.display_name, ' | ')
                    FROM salesitem si
                    LEFT JOIN product pr ON pr.id = si.product_id
                    WHERE si.sales_id = s.id
                ) AS products,
                s.received,
                s.creation_date
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            WHERE s.creation_date BETWEEN ? AND ?
              AND (
                ? = ''
                OR c.name LIKE ?
                OR (s.customer IS NULL AND 'Walk-in Customer' LIKE ?)
              )
            ORDER BY s.id DESC
            """
        )
        query.addBindValue(from_date)
        query.addBindValue(to_date)
        query.addBindValue(search_text)
        query.addBindValue(pattern)
        query.addBindValue(pattern)

    if not query.exec():
        raise Exception(f"Failed to load sales receipt rows: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "sales_id": int(query.value(0) or 0),
                "customer_name": str(query.value(1) or "Walk-in Customer"),
                "products": str(query.value(2) or ""),
                "received": str(query.value(3) or ""),
                "creation_date": _format_date(query.value(4)),
            }
        )
    return rows


def fetch_saved_sale_tax_breakdown(sales_id):
    header_tax = 0.0
    line_tax = 0.0

    header_query = _new_query()
    header_query.prepare("SELECT COALESCE(tax, 0) FROM sales WHERE id = ? LIMIT 1")
    header_query.addBindValue(int(sales_id))
    if header_query.exec() and header_query.next():
        header_tax = float(header_query.value(0) or 0.0)

    line_query = _new_query()
    line_query.prepare("SELECT COALESCE(SUM(COALESCE(tax_amount, 0)), 0) FROM salesitem WHERE sales_id = ?")
    line_query.addBindValue(int(sales_id))
    if line_query.exec() and line_query.next():
        line_tax = float(line_query.value(0) or 0.0)

    policy = load_sales_policy_settings().get("tax_policy", "both")

    return {
        "line_tax": line_tax,
        "header_tax": header_tax,
        "policy": policy,
    }


def fetch_active_customer_option_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT id, name
        FROM customer
        WHERE status = 'active'
        ORDER BY name ASC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load customers: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "customer_id": query.value(0),
                "name": str(query.value(1) or "").strip(),
            }
        )
    return rows


def create_sales_customer(name, contact=None):
    name = str(name or "").strip()
    contact = str(contact or "").strip()
    if not name:
        raise ValueError("Customer name is required.")

    query = _new_query()
    query.prepare(
        """
        INSERT INTO customer (
            name,
            contact
        )
        VALUES (?, ?)
        """
    )
    query.addBindValue(name)
    query.addBindValue(contact if contact else None)

    if not query.exec():
        raise Exception(f"Failed to save customer: {query.lastError().text()}")

    customer_id = query.lastInsertId()
    try:
        customer_id = int(customer_id)
    except Exception:
        customer_id = None
    return customer_id


def insert_sales_customer_quick(name):
    name = str(name or "").strip()
    if not name:
        return None

    query = _new_query()
    query.prepare(
        """
        INSERT INTO customer (name, contact, email, payable, receiveable, status)
        VALUES (?, ?, ?, ?, ?, 'active')
        """
    )
    query.addBindValue(name)
    query.addBindValue("")
    query.addBindValue("")
    query.addBindValue(0.0)
    query.addBindValue(0.0)

    if not query.exec():
        raise Exception(f"Insert customer failed: {query.lastError().text()}")

    return query.lastInsertId()


def fetch_active_manufacturer_option_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT id, name
        FROM manufacturer
        WHERE status = 'active'
        ORDER BY name
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load manufacturers: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "manufacturer_id": query.value(0),
                "name": str(query.value(1) or "").strip(),
            }
        )
    return rows


def ensure_sales_manufacturer(name):
    normalized_name = str(name or "").strip()
    if not normalized_name:
        return None

    query = _new_query()
    query.prepare(
        """
        SELECT id, name
        FROM manufacturer
        WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
        LIMIT 1
        """
    )
    query.addBindValue(normalized_name)
    if not query.exec():
        raise Exception(f"Failed to check manufacturer: {query.lastError().text()}")
    if query.next():
        return {
            "manufacturer_id": query.value(0),
            "name": str(query.value(1) or normalized_name).strip() or normalized_name,
            "created": False,
        }

    insert_query = _new_query()
    insert_query.prepare("INSERT INTO manufacturer (name) VALUES (?)")
    insert_query.addBindValue(normalized_name)
    if not insert_query.exec():
        raise Exception(f"Failed to save manufacturer: {insert_query.lastError().text()}")

    manufacturer_id = insert_query.lastInsertId()
    try:
        manufacturer_id = int(manufacturer_id)
    except Exception:
        pass

    return {
        "manufacturer_id": manufacturer_id,
        "name": normalized_name,
        "created": True,
    }


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
    ensure_prescription_schema()
    prescription = fetch_sales_prescription_by_sales_id(sales_id)
    attachments = []
    if prescription:
        attachments = fetch_sales_prescription_attachments(prescription["id"])
    return {
        "header": header,
        "items": fetch_sales_detail_items(sales_id),
        "business": fetch_business_identity(),
        "prescription": prescription,
        "prescription_attachments": attachments,
    }


def fetch_sales_receipt_render_context(sales_id):
    header = fetch_sales_detail(sales_id)
    if not header:
        return None

    return {
        "business": fetch_business_identity(),
        "header": header,
        "items": fetch_sales_detail_items(sales_id),
        "tax_breakdown": fetch_saved_sale_tax_breakdown(sales_id),
    }


def fetch_hold_sale_detail(hold_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            customer, salesman, subtotal, discount_amount, taxable_amount,
            tax_amount, additional_charges, final_amount, received_amount,
            remaining_amount, payment_method, due_date
        FROM holdsale
        WHERE id = ?
        """
    )
    query.addBindValue(int(hold_id))

    if not query.exec():
        raise Exception(f"Unable to load held sale: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "customer_id": query.value(0),
        "salesman_id": query.value(1),
        "subtotal": float(query.value(2) or 0.0),
        "discount_amount": float(query.value(3) or 0.0),
        "taxable_amount": float(query.value(4) or 0.0),
        "tax_amount": float(query.value(5) or 0.0),
        "additional_charges": float(query.value(6) or 0.0),
        "final_amount": float(query.value(7) or 0.0),
        "received_amount": float(query.value(8) or 0.0),
        "remaining_amount": float(query.value(9) or 0.0),
        "payment_method": str(query.value(10) or "Cash").strip() or "Cash",
        "due_date": str(query.value(11) or "").strip(),
    }


def fetch_hold_sale_item_rows(hold_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            product, qty, unitrate, discount, discountamount,
            COALESCE(tax, 0), COALESCE(discount_input_mode, 'percent'), total
        FROM holditems
        WHERE holdsale = ?
        """
    )
    query.addBindValue(int(hold_id))

    if not query.exec():
        raise Exception(f"Unable to load held sale items: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "product_id": int(query.value(0) or 0),
                "qty": int(query.value(1) or 0),
                "unitrate": float(query.value(2) or 0.0),
                "discount_percent": float(query.value(3) or 0.0),
                "discount_amount": float(query.value(4) or 0.0),
                "tax_percent": float(query.value(5) or 0.0),
                "discount_input_mode": str(query.value(6) or "percent"),
                "total": float(query.value(7) or 0.0),
            }
        )
    return rows


def fetch_hold_sale_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            h.id,
            COALESCE(c.name, 'Walk-in Customer') AS customer_name,
            COALESCE(a.username, e.name, '-') AS user_name,
            COALESCE(h.final_amount, 0),
            COALESCE((SELECT COUNT(*) FROM holditems hi WHERE hi.holdsale = h.id), 0),
            h.creation_date
        FROM holdsale h
        LEFT JOIN customer c ON c.id = h.customer
        LEFT JOIN auth a ON a.id = h.salesman
        LEFT JOIN employee e ON e.id = h.salesman
        ORDER BY h.id DESC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load held sales: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "customer": str(query.value(1) or "Walk-in Customer"),
                "user": str(query.value(2) or "-"),
                "final_amount": float(query.value(3) or 0.0),
                "items": int(query.value(4) or 0),
                "created_at": str(query.value(5) or "-"),
            }
        )
    return rows
