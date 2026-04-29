def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


import mimetypes
import os
import shutil
from datetime import datetime
from medic.utilities.database import SQLiteConnectionManager


from medic.services.inventory_movement_service import (
    decrement_batch_quantity as decrement_batch_quantity_from_inventory,
    fetch_fifo_batch_rows as fetch_fifo_batch_rows_from_inventory,
    fetch_total_available_stock as fetch_total_available_stock_from_inventory,
    insert_sold_batch_record as insert_sold_batch_record_from_inventory,
)
from medic.services.sales_items_service import compute_fifo_allocation_plan


def ensure_prescription_schema():
    query = _new_query()

    has_prescription_required = False
    if not query.exec("PRAGMA table_info(product)"):
        raise Exception(f"Product schema check failed: {query.lastError().text()}")

    while query.next():
        if str(query.value(1) or "").strip().lower() == "prescription_required":
            has_prescription_required = True
            break

    if not has_prescription_required:
        if not query.exec("ALTER TABLE product ADD COLUMN prescription_required INTEGER NOT NULL DEFAULT 0"):
            raise Exception(f"Product prescription migration failed: {query.lastError().text()}")

    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS sales_prescription (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_id INTEGER NOT NULL UNIQUE,
            doctor_name TEXT NOT NULL,
            clinic_name TEXT,
            doctor_license_no TEXT,
            prescription_date TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (sales_id) REFERENCES sales(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES auth(id) ON DELETE SET NULL
        )
        """
    ):
        raise Exception(f"Sales prescription table creation failed: {query.lastError().text()}")

    if not query.exec(
        "CREATE INDEX IF NOT EXISTS idx_sales_prescription_sales_id ON sales_prescription(sales_id)"
    ):
        raise Exception(f"Sales prescription index creation failed: {query.lastError().text()}")

    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS sales_prescription_attachment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_prescription_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            mime_type TEXT,
            file_size INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER,
            FOREIGN KEY (sales_prescription_id) REFERENCES sales_prescription(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES auth(id) ON DELETE SET NULL
        )
        """
    ):
        raise Exception(f"Sales prescription attachment table creation failed: {query.lastError().text()}")

    if not query.exec(
        "CREATE INDEX IF NOT EXISTS idx_sales_prescription_attachment_rx_id ON sales_prescription_attachment(sales_prescription_id)"
    ):
        raise Exception(f"Sales prescription attachment index creation failed: {query.lastError().text()}")

    return True


def get_prescription_attachment_dir():
    manager = SQLiteConnectionManager("ProcureApp")
    attachment_dir = manager.get_prescription_storage_dir()
    os.makedirs(attachment_dir, exist_ok=True)
    _migrate_legacy_prescription_files(attachment_dir)
    return attachment_dir


def _get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_legacy_prescription_attachment_dir():
    return os.path.join(_get_project_root(), "storage", "prescriptions")


def _migrate_legacy_prescription_files(target_dir):
    legacy_dir = _get_legacy_prescription_attachment_dir()
    if not os.path.isdir(legacy_dir):
        return
    for name in os.listdir(legacy_dir):
        source_path = os.path.join(legacy_dir, name)
        target_path = os.path.join(target_dir, name)
        if not os.path.isfile(source_path) or os.path.exists(target_path):
            continue
        try:
            shutil.copy2(source_path, target_path)
        except OSError:
            continue


def fetch_prescription_required_products(product_ids):
    normalized_ids = []
    for product_id in product_ids or []:
        try:
            normalized_ids.append(int(product_id))
        except (TypeError, ValueError):
            continue

    if not normalized_ids:
        return []

    placeholders = ", ".join("?" for _ in normalized_ids)
    query = _new_query()
    query.prepare(
        f"""
        SELECT id, COALESCE(display_name, '')
        FROM product
        WHERE id IN ({placeholders})
          AND COALESCE(prescription_required, 0) = 1
        ORDER BY display_name ASC
        """
    )
    for product_id in normalized_ids:
        query.addBindValue(product_id)

    if not query.exec():
        raise Exception(f"Failed to load prescription-required products: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "product_id": int(query.value(0) or 0),
                "display_name": str(query.value(1) or "").strip(),
            }
        )
    return rows


def insert_sales_prescription_record(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO sales_prescription (
            sales_id,
            doctor_name,
            clinic_name,
            doctor_license_no,
            prescription_date,
            notes,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(payload["sales_id"])
    query.addBindValue(payload["doctor_name"])
    query.addBindValue(payload.get("clinic_name") or None)
    query.addBindValue(payload.get("doctor_license_no") or None)
    query.addBindValue(payload.get("prescription_date") or None)
    query.addBindValue(payload.get("notes") or None)
    query.addBindValue(payload.get("created_by"))

    if not query.exec():
        raise Exception(f"Failed to save sales prescription: {query.lastError().text()}")

    return query.lastInsertId()


def insert_sales_prescription_attachment_record(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO sales_prescription_attachment (
            sales_prescription_id,
            original_filename,
            stored_filename,
            relative_path,
            mime_type,
            file_size,
            uploaded_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(payload["sales_prescription_id"])
    query.addBindValue(payload["original_filename"])
    query.addBindValue(payload["stored_filename"])
    query.addBindValue(payload["relative_path"])
    query.addBindValue(payload.get("mime_type") or None)
    query.addBindValue(payload.get("file_size") or 0)
    query.addBindValue(payload.get("uploaded_by"))

    if not query.exec():
        raise Exception(f"Failed to save sales prescription attachment: {query.lastError().text()}")

    return query.lastInsertId()


def save_sales_prescription_attachment(*, sales_prescription_id, sales_id, source_path, uploaded_by=None):
    source_path = str(source_path or "").strip()
    if not source_path:
        return None
    if not os.path.exists(source_path):
        raise Exception("Prescription attachment file could not be found.")

    attachment_dir = get_prescription_attachment_dir()
    original_filename = os.path.basename(source_path)
    _, extension = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_filename = f"rx_sale_{int(sales_id)}_{timestamp}{extension.lower()}"
    destination_path = os.path.join(attachment_dir, stored_filename)
    shutil.copy2(source_path, destination_path)

    mime_type = mimetypes.guess_type(original_filename)[0] or ""
    file_size = 0
    try:
        file_size = int(os.path.getsize(destination_path))
    except OSError:
        file_size = 0

    relative_path = os.path.join("prescriptions", stored_filename)
    payload = {
        "sales_prescription_id": sales_prescription_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "relative_path": relative_path,
        "mime_type": mime_type,
        "file_size": file_size,
        "uploaded_by": uploaded_by,
    }
    insert_sales_prescription_attachment_record(payload)
    return payload


def fetch_sales_prescription_by_sales_id(sales_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            COALESCE(doctor_name, ''),
            COALESCE(clinic_name, ''),
            COALESCE(doctor_license_no, ''),
            COALESCE(prescription_date, ''),
            COALESCE(notes, ''),
            COALESCE(created_at, ''),
            COALESCE(created_by, 0)
        FROM sales_prescription
        WHERE sales_id = ?
        LIMIT 1
        """
    )
    query.addBindValue(sales_id)
    if not query.exec():
        raise Exception(f"Failed to load sales prescription: {query.lastError().text()}")
    if not query.next():
        return None
    return {
        "id": int(query.value(0) or 0),
        "doctor_name": str(query.value(1) or "").strip(),
        "clinic_name": str(query.value(2) or "").strip(),
        "doctor_license_no": str(query.value(3) or "").strip(),
        "prescription_date": str(query.value(4) or "").strip(),
        "notes": str(query.value(5) or "").strip(),
        "created_at": str(query.value(6) or "").strip(),
        "created_by": int(query.value(7) or 0) or None,
    }


def fetch_sales_prescription_attachments(sales_prescription_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            COALESCE(original_filename, ''),
            COALESCE(stored_filename, ''),
            COALESCE(relative_path, ''),
            COALESCE(mime_type, ''),
            COALESCE(file_size, 0),
            COALESCE(uploaded_at, '')
        FROM sales_prescription_attachment
        WHERE sales_prescription_id = ?
        ORDER BY uploaded_at ASC, id ASC
        """
    )
    query.addBindValue(sales_prescription_id)
    if not query.exec():
        raise Exception(f"Failed to load sales prescription attachments: {query.lastError().text()}")

    rows = []
    attachment_root = get_prescription_attachment_dir()
    while query.next():
        relative_path = str(query.value(3) or "").strip()
        if relative_path.startswith("storage/") or relative_path.startswith("storage\\"):
            absolute_path = os.path.normpath(os.path.join(_get_project_root(), relative_path))
            if not os.path.exists(absolute_path):
                absolute_path = os.path.normpath(os.path.join(attachment_root, os.path.basename(relative_path)))
        else:
            absolute_path = os.path.normpath(os.path.join(os.path.dirname(attachment_root), relative_path)) if relative_path else ""
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "original_filename": str(query.value(1) or "").strip(),
                "stored_filename": str(query.value(2) or "").strip(),
                "relative_path": relative_path,
                "absolute_path": absolute_path,
                "mime_type": str(query.value(4) or "").strip(),
                "file_size": int(query.value(5) or 0),
                "uploaded_at": str(query.value(6) or "").strip(),
            }
        )
    return rows


def build_customer_transaction_payload(
    *,
    sales_id,
    customer_id,
    total_amount,
    received,
    salesman_id,
    session_id,
    payment,
    note,
    balance_state,
):
    balance_state = dict(balance_state or {})
    payment = dict(payment or {})
    return {
        "customer_id": customer_id,
        "transaction_type": "SALE",
        "ref": sales_id,
        "return_ref": None,
        "payable_before": float(balance_state.get("payable_before") or 0.0),
        "due_amount": float(total_amount or 0.0),
        "paid": 0.0,
        "remaining_due": float(balance_state.get("remaining_due") or 0.0),
        "payable_after": float(balance_state.get("payable_after") or 0.0),
        "receiveable_before": float(balance_state.get("receiveable_before") or 0.0),
        "receiveable_now": float(balance_state.get("receiveable_now") or 0.0),
        "received": float(received or 0.0),
        "remaining_now": float(balance_state.get("remaining_now") or 0.0),
        "receiveable_after": float(balance_state.get("receiveable_after") or 0.0),
        "payment_method": payment.get("payment_method"),
        "bank_name": payment.get("bank_name"),
        "account_no": payment.get("account_no"),
        "transaction_mode": payment.get("transaction_mode"),
        "wallet_provider": payment.get("wallet_provider"),
        "wallet_no": payment.get("wallet_no"),
        "payment_reference": payment.get("payment_reference"),
        "salesman_id": salesman_id,
        "note": note,
        "session_id": session_id,
    }


def insert_sales_header(header_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO sales
        (customer, salesman, subtotal, discount, taxable, tax,
        net_amount, additional_charges, total, received,
        remaining, writeoff, payable, receiveable, session_id, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(header_payload["customer_id"])
    query.addBindValue(header_payload["salesman_id"])
    query.addBindValue(header_payload["subtotal"])
    query.addBindValue(header_payload["discount"])
    query.addBindValue(header_payload["taxable"])
    query.addBindValue(header_payload["tax"])
    query.addBindValue(header_payload["net_amount"])
    query.addBindValue(header_payload["additional_charges"])
    query.addBindValue(header_payload["total"])
    query.addBindValue(header_payload["received"])
    query.addBindValue(header_payload["remaining"])
    query.addBindValue(header_payload["writeoff"])
    query.addBindValue(header_payload["payable"])
    query.addBindValue(header_payload["receiveable"])
    query.addBindValue(header_payload["session_id"])
    query.addBindValue(header_payload["due_date"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return query.lastInsertId()


def fetch_customer_balances(customer_id):
    query = _new_query()
    query.prepare(
        """
        SELECT payable, receiveable
        FROM customer
        WHERE id = ?
        """
    )
    query.addBindValue(customer_id)

    if not query.exec() or not query.next():
        raise Exception("Failed to fetch customer balance.")

    return {
        "payable_before": float(query.value(0) or 0.0),
        "receiveable_before": float(query.value(1) or 0.0),
    }


def insert_customer_transaction_record(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO customer_transaction
        (
            customer, transaction_type, ref, return_ref,
            payable_before, due_amount, paid, remaining_due, payable_after,
            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
            payment_method, bank_name, account_no, transaction_mode,
            wallet_provider, wallet_no, payment_reference,
            salesman, note, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(payload["customer_id"])
    query.addBindValue(payload["transaction_type"])
    query.addBindValue(payload["ref"])
    query.addBindValue(payload["return_ref"])
    query.addBindValue(payload["payable_before"])
    query.addBindValue(payload["due_amount"])
    query.addBindValue(payload["paid"])
    query.addBindValue(payload["remaining_due"])
    query.addBindValue(payload["payable_after"])
    query.addBindValue(payload["receiveable_before"])
    query.addBindValue(payload["receiveable_now"])
    query.addBindValue(payload["received"])
    query.addBindValue(payload["remaining_now"])
    query.addBindValue(payload["receiveable_after"])
    query.addBindValue(payload.get("payment_method") or None)
    query.addBindValue(payload.get("bank_name") or None)
    query.addBindValue(payload.get("account_no") or None)
    query.addBindValue(payload.get("transaction_mode") or None)
    query.addBindValue(payload.get("wallet_provider") or None)
    query.addBindValue(payload.get("wallet_no") or None)
    query.addBindValue(payload.get("payment_reference") or None)
    query.addBindValue(payload["salesman_id"])
    query.addBindValue(payload["note"])
    query.addBindValue(payload["session_id"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return query.lastInsertId()


def update_customer_running_balance(customer_id, *, payable_after, receiveable_after):
    query = _new_query()
    query.prepare(
        """
        UPDATE customer
        SET payable = ?, receiveable = ?
        WHERE id = ?
        """
    )
    query.addBindValue(payable_after)
    query.addBindValue(receiveable_after)
    query.addBindValue(customer_id)

    if not query.exec():
        raise Exception(query.lastError().text())

    return True


def fetch_total_available_stock(product_id):
    return fetch_total_available_stock_from_inventory(product_id)


def insert_sales_item_record(sales_id, row_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO salesitem
        (sales_id, product_id, qty_sold, unit_price,
        discount, tax, discount_amount, tax_amount, discount_input_mode,
        default_discount_group_id, default_tax_group_id,
        discount_group_id, tax_group_id, discount_source, tax_source,
        line_total, line_weight, effective_line_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(sales_id)
    query.addBindValue(row_payload["product_id"])
    query.addBindValue(row_payload["qty"])
    query.addBindValue(row_payload["rate"])
    query.addBindValue(row_payload["discount_percent"])
    query.addBindValue(row_payload["tax_percent"])
    query.addBindValue(row_payload["discount_amount"])
    query.addBindValue(row_payload["tax_amount"])
    query.addBindValue(row_payload["discount_input_mode"])
    query.addBindValue(row_payload["default_discount_group_id"])
    query.addBindValue(row_payload["default_tax_group_id"])
    query.addBindValue(row_payload["discount_group_id"])
    query.addBindValue(row_payload["tax_group_id"])
    query.addBindValue(row_payload["discount_source"])
    query.addBindValue(row_payload["tax_source"])
    query.addBindValue(row_payload["line_total"])
    query.addBindValue(row_payload["line_weight"])
    query.addBindValue(row_payload["effective_line_total"])

    if not query.exec():
        raise Exception(f"Failed to insert sales item: {query.lastError().text()}")

    return query.lastInsertId()


def fetch_fifo_batch_rows(product_id):
    return fetch_fifo_batch_rows_from_inventory(product_id)


def decrement_batch_quantity(batch_id, take_qty):
    return decrement_batch_quantity_from_inventory(batch_id, take_qty)


def insert_sold_batch_record(sale_item_id, allocation):
    return insert_sold_batch_record_from_inventory(sale_item_id, allocation)


def resolve_salesman_id(username):
    query = _new_query()
    query.prepare("SELECT id FROM auth WHERE username = ?;")
    query.addBindValue(username)
    if not query.exec():
        raise Exception(query.lastError().text())
    if not query.next():
        raise Exception("Salesman account not found.")
    return query.value(0)


def fetch_customer_credit_position(customer_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            COALESCE(name, 'Walk-in Customer'),
            COALESCE(receiveable, 0),
            COALESCE(credit_limit, 0)
        FROM customer
        WHERE id = ?
        """
    )
    query.addBindValue(customer_id)
    if not query.exec() or not query.next():
        raise Exception("Could not load customer credit information.")
    return {
        "customer_name": str(query.value(0) or ""),
        "current_receivable": float(query.value(1) or 0.0),
        "credit_limit": float(query.value(2) or 0.0),
    }


def persist_sales_customer_transaction(
    *,
    sales_id,
    customer_id,
    total_amount,
    received,
    remaining,
    salesman_id,
    session_id,
    payment,
):
    payable_before = 0.0
    receiveable_before = 0.0
    balance_state = compute_customer_transaction_balances(
        payable_before=0.0,
        receiveable_before=0.0,
        remaining=remaining,
    )

    if customer_id is not None:
        existing_balances = fetch_customer_balances(customer_id)
        payable_before = existing_balances["payable_before"]
        receiveable_before = existing_balances["receiveable_before"]
        balance_state = compute_customer_transaction_balances(
            payable_before=payable_before,
            receiveable_before=receiveable_before,
            remaining=remaining,
        )

    note = build_customer_transaction_note(
        sales_id=sales_id,
        total_amount=total_amount,
        received=received,
        remaining=remaining,
    )
    txn_payload = build_customer_transaction_payload(
        sales_id=sales_id,
        customer_id=customer_id,
        total_amount=float(total_amount or 0.0),
        received=float(received or 0.0),
        salesman_id=salesman_id,
        session_id=session_id,
        payment=payment,
        note=note,
        balance_state=balance_state,
    )
    transaction_id = insert_customer_transaction_record(txn_payload)

    if customer_id is not None:
        update_customer_running_balance(
            customer_id,
            payable_after=balance_state["payable_after"],
            receiveable_after=balance_state["receiveable_after"],
        )

    return {
        "transaction_id": transaction_id,
        "balance_state": balance_state,
        "payable_before": payable_before,
        "receiveable_before": receiveable_before,
    }


def persist_sales_receipt_header_and_prescription(
    header_payload, sales_prescription_payload=None
):
    sales_id = insert_sales_header(header_payload)

    if sales_prescription_payload:
        prescription_payload = dict(sales_prescription_payload)
        attachment_source_paths = list(
            prescription_payload.pop("attachment_source_paths", []) or []
        )
        prescription_payload["sales_id"] = sales_id
        prescription_id = insert_sales_prescription_record(prescription_payload)
        for attachment_source_path in attachment_source_paths:
            if not attachment_source_path:
                continue
            save_sales_prescription_attachment(
                sales_prescription_id=int(prescription_id),
                sales_id=sales_id,
                source_path=attachment_source_path,
                uploaded_by=prescription_payload.get("created_by"),
            )

    return sales_id


def persist_sales_item_with_fifo(*, sales_id, row_payload, row_number):
    product_id = int(row_payload.get("product_id") or 0)
    qty_needed = float(row_payload.get("qty") or 0.0)

    total_available = float(fetch_total_available_stock(product_id) or 0.0)
    if total_available < qty_needed:
        raise Exception(
            f"Row {row_number}: Insufficient stock for product ID {product_id}. "
            f"Available: {total_available:g}, required: {qty_needed:g}"
        )

    sale_item_id = insert_sales_item_record(sales_id, row_payload)
    batch_rows = fetch_fifo_batch_rows(product_id)
    allocation_result = compute_fifo_allocation_plan(batch_rows, qty_needed)

    remaining_qty = float(allocation_result.get("remaining_qty") or 0.0)
    if remaining_qty > 0:
        raise Exception(
            f"FIFO allocation failed for product ID {product_id}. "
            f"Unallocated qty: {remaining_qty:g}"
        )

    for allocation in allocation_result.get("allocations", []):
        decrement_batch_quantity(allocation["batch_id"], allocation["take_qty"])
        insert_sold_batch_record(sale_item_id, allocation)

    return {
        "sale_item_id": sale_item_id,
        "total_available": total_available,
        "allocation_result": allocation_result,
    }


def upsert_hold_sale_header(payload, hold_id=None):
    query = _new_query()

    if hold_id is not None:
        query.prepare(
            """
            UPDATE holdsale
            SET customer = ?, salesman = ?, status = ?,
                subtotal = ?, discount_amount = ?, taxable_amount = ?, tax_amount = ?,
                additional_charges = ?, final_amount = ?, received_amount = ?,
                remaining_amount = ?, payment_method = ?, due_date = ?
            WHERE id = ?
            """
        )
    else:
        query.prepare(
            """
            INSERT INTO holdsale (
                customer, salesman, status,
                subtotal, discount_amount, taxable_amount, tax_amount,
                additional_charges, final_amount, received_amount,
                remaining_amount, payment_method, due_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )

    query.addBindValue(payload.get("customer"))
    query.addBindValue(payload.get("salesman"))
    query.addBindValue(payload.get("status"))
    query.addBindValue(payload.get("subtotal"))
    query.addBindValue(payload.get("discount_amount"))
    query.addBindValue(payload.get("taxable_amount"))
    query.addBindValue(payload.get("tax_amount"))
    query.addBindValue(payload.get("additional_charges"))
    query.addBindValue(payload.get("final_amount"))
    query.addBindValue(payload.get("received_amount"))
    query.addBindValue(payload.get("remaining_amount"))
    query.addBindValue(payload.get("payment_method"))
    query.addBindValue(payload.get("due_date"))

    if hold_id is not None:
        query.addBindValue(int(hold_id))

    if not query.exec():
        raise Exception(query.lastError().text())

    if hold_id is None:
        hold_id = query.lastInsertId()

    try:
        return int(hold_id)
    except Exception:
        return hold_id


def replace_hold_sale_items(hold_id, item_rows):
    hold_id = int(hold_id)

    clear_query = _new_query()
    clear_query.prepare("DELETE FROM holditems WHERE holdsale = ?")
    clear_query.addBindValue(hold_id)
    if not clear_query.exec():
        raise Exception(clear_query.lastError().text())

    for row in item_rows:
        item_query = _new_query()
        item_query.prepare(
            """
            INSERT INTO holditems (
                holdsale, product, qty, unitrate, discount,
                discountamount, tax, taxamount, discount_input_mode, total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )
        item_query.addBindValue(hold_id)
        item_query.addBindValue(row["product_id"])
        item_query.addBindValue(row["qty"])
        item_query.addBindValue(row["rate"])
        item_query.addBindValue(row["discount"])
        item_query.addBindValue(row["discountamount"])
        item_query.addBindValue(row["tax"])
        item_query.addBindValue(row["taxamount"])
        item_query.addBindValue(row["discount_input_mode"])
        item_query.addBindValue(row["total"])

        if not item_query.exec():
            raise Exception(
                f"Failed to insert hold item for product_id {row['product_id']}: "
                f"{item_query.lastError().text()}"
            )


def delete_hold_sale(hold_id):
    hold_id = int(hold_id)

    item_delete = _new_query()
    item_delete.prepare("DELETE FROM holditems WHERE holdsale = ?")
    item_delete.addBindValue(hold_id)
    if not item_delete.exec():
        raise Exception(item_delete.lastError().text())

    hold_delete = _new_query()
    hold_delete.prepare("DELETE FROM holdsale WHERE id = ?")
    hold_delete.addBindValue(hold_id)
    if not hold_delete.exec():
        raise Exception(hold_delete.lastError().text())
