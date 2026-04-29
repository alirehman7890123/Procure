from PySide6.QtSql import QSqlDatabase, QSqlQuery

try:
    from medic.utilities.session_service import get_active_session_id
except ModuleNotFoundError:
    from utilities.session_service import get_active_session_id


def _new_query():
    return QSqlQuery()


def _read_rows(query, columns):
    rows = []
    while query.next():
        row = {}
        for index, column in enumerate(columns):
            row[column] = query.value(index)
        rows.append(row)
    return rows


def fetch_customer_transaction_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            ct.id,
            COALESCE(c.name, 'Walk-in Customer') AS customer_name,
            ct.transaction_type,
            COALESCE(ct.paid, 0),
            COALESCE(ct.received, 0),
            ct.creation_date
        FROM customer_transaction ct
        LEFT JOIN customer c ON ct.customer = c.id
        WHERE ct.customer IS NOT NULL
        ORDER BY ct.id DESC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load customer transactions: {query.lastError().text()}")

    return _read_rows(
        query,
        [
            "transaction_id",
            "customer_name",
            "transaction_type",
            "paid",
            "received",
            "creation_date",
        ],
    )


def fetch_supplier_transaction_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            st.id,
            COALESCE(s.name, '') AS supplier_name,
            st.transaction_type,
            COALESCE(st.paid, 0),
            COALESCE(st.received, 0),
            st.creation_date
        FROM supplier_transaction st
        LEFT JOIN supplier s ON st.supplier = s.id
        ORDER BY st.id DESC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load supplier transactions: {query.lastError().text()}")

    return _read_rows(
        query,
        [
            "transaction_id",
            "supplier_name",
            "transaction_type",
            "paid",
            "received",
            "creation_date",
        ],
    )


def fetch_customer_transaction_detail(transaction_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            ct.id,
            ct.customer,
            COALESCE(c.name, 'Walk-in Customer') AS customer_name,
            COALESCE(c.contact, '-') AS customer_contact,
            ct.transaction_type,
            ct.ref,
            ct.return_ref,
            COALESCE(ct.payable_before, 0),
            COALESCE(ct.due_amount, 0),
            COALESCE(ct.paid, 0),
            COALESCE(ct.remaining_due, 0),
            COALESCE(ct.payable_after, 0),
            COALESCE(ct.receiveable_before, 0),
            COALESCE(ct.receiveable_now, 0),
            COALESCE(ct.received, 0),
            COALESCE(ct.remaining_now, 0),
            COALESCE(ct.receiveable_after, 0),
            ct.salesman,
            COALESCE(e.name, '-') AS salesman_name,
            ct.note,
            ct.creation_date
        FROM customer_transaction ct
        LEFT JOIN customer c ON ct.customer = c.id
        LEFT JOIN employee e ON ct.salesman = e.id
        WHERE ct.id = ?
        LIMIT 1
        """
    )
    query.addBindValue(transaction_id)

    if not query.exec():
        raise Exception(f"Failed to load customer transaction detail: {query.lastError().text()}")

    rows = _read_rows(
        query,
        [
            "transaction_id",
            "customer_id",
            "customer_name",
            "customer_contact",
            "transaction_type",
            "ref",
            "return_ref",
            "payable_before",
            "due_amount",
            "paid",
            "remaining_due",
            "payable_after",
            "receiveable_before",
            "receiveable_now",
            "received",
            "remaining_now",
            "receiveable_after",
            "salesman_id",
            "salesman_name",
            "note",
            "creation_date",
        ],
    )
    return rows[0] if rows else None


def fetch_supplier_transaction_detail(transaction_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            st.id,
            st.supplier,
            COALESCE(s.name, '-') AS supplier_name,
            COALESCE(s.contact, '-') AS supplier_contact,
            st.transaction_type,
            st.ref,
            st.return_ref,
            COALESCE(st.payable_before, 0),
            COALESCE(st.due_amount, 0),
            COALESCE(st.paid, 0),
            COALESCE(st.remaining_due, 0),
            COALESCE(st.payable_after, 0),
            COALESCE(st.receiveable_before, 0),
            COALESCE(st.receiveable_now, 0),
            COALESCE(st.received, 0),
            COALESCE(st.remaining_now, 0),
            COALESCE(st.receiveable_after, 0),
            st.rep,
            COALESCE(r.name, '-') AS rep_name,
            st.note,
            st.creation_date
        FROM supplier_transaction st
        LEFT JOIN supplier s ON st.supplier = s.id
        LEFT JOIN rep r ON st.rep = r.id
        WHERE st.id = ?
        LIMIT 1
        """
    )
    query.addBindValue(transaction_id)

    if not query.exec():
        raise Exception(f"Failed to load supplier transaction detail: {query.lastError().text()}")

    rows = _read_rows(
        query,
        [
            "transaction_id",
            "supplier_id",
            "supplier_name",
            "supplier_contact",
            "transaction_type",
            "ref",
            "return_ref",
            "payable_before",
            "due_amount",
            "paid",
            "remaining_due",
            "payable_after",
            "receiveable_before",
            "receiveable_now",
            "received",
            "remaining_now",
            "receiveable_after",
            "rep_id",
            "rep_name",
            "note",
            "creation_date",
        ],
    )
    return rows[0] if rows else None


def fetch_customer_balance_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            COALESCE(name, '') AS name,
            COALESCE(contact, '') AS contact,
            COALESCE(email, '') AS email,
            COALESCE(payable, 0) AS payable,
            COALESCE(receiveable, 0) AS receiveable
        FROM customer
        ORDER BY name ASC, id ASC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load customers: {query.lastError().text()}")

    return _read_rows(
        query,
        ["party_id", "name", "contact", "email", "payable", "receiveable"],
    )


def fetch_supplier_balance_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            COALESCE(name, '') AS name,
            COALESCE(contact, '') AS contact,
            COALESCE(email, '') AS email,
            COALESCE(payable, 0) AS payable,
            COALESCE(receiveable, 0) AS receiveable
        FROM supplier
        ORDER BY name ASC, id ASC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load suppliers: {query.lastError().text()}")

    return _read_rows(
        query,
        ["party_id", "name", "contact", "email", "payable", "receiveable"],
    )


def fetch_transaction_dashboard_summary():
    return {
        "supplier": _fetch_party_balance_summary("supplier"),
        "customer": _fetch_party_balance_summary("customer"),
    }


def reconcile_customer_internal_balance(customer_id):
    return _reconcile_internal_balance("customer", int(customer_id))


def reconcile_supplier_internal_balance(supplier_id):
    return _reconcile_internal_balance("supplier", int(supplier_id))


def fetch_customer_transaction_form_context(customer_id):
    customer_query = _new_query()
    customer_query.prepare(
        """
        SELECT id, COALESCE(name, ''), COALESCE(contact, ''), COALESCE(payable, 0), COALESCE(receiveable, 0)
        FROM customer
        WHERE id = ?
        LIMIT 1
        """
    )
    customer_query.addBindValue(int(customer_id))
    if not customer_query.exec() or not customer_query.next():
        raise Exception("Customer not found.")

    employee_query = _new_query()
    employee_query.prepare("SELECT id, COALESCE(name, ''), COALESCE(contact, '') FROM employee ORDER BY name ASC, id ASC")
    if not employee_query.exec():
        raise Exception(f"Failed to load employees: {employee_query.lastError().text()}")

    salesmen = []
    while employee_query.next():
        salesmen.append(
            {
                "id": int(employee_query.value(0) or 0),
                "name": str(employee_query.value(1) or ""),
                "contact": str(employee_query.value(2) or ""),
            }
        )

    return {
        "customer_id": int(customer_query.value(0) or 0),
        "customer_name": str(customer_query.value(1) or ""),
        "customer_contact": str(customer_query.value(2) or ""),
        "payable": float(customer_query.value(3) or 0.0),
        "receiveable": float(customer_query.value(4) or 0.0),
        "salesmen": salesmen,
    }


def fetch_supplier_transaction_form_context(supplier_id):
    supplier_query = _new_query()
    supplier_query.prepare(
        """
        SELECT id, COALESCE(name, ''), COALESCE(contact, ''), COALESCE(address, ''), COALESCE(payable, 0), COALESCE(receiveable, 0)
        FROM supplier
        WHERE id = ?
        LIMIT 1
        """
    )
    supplier_query.addBindValue(int(supplier_id))
    if not supplier_query.exec() or not supplier_query.next():
        raise Exception("Supplier not found.")

    rep_query = _new_query()
    rep_query.prepare(
        """
        SELECT id, COALESCE(name, ''), COALESCE(contact, '')
        FROM rep
        WHERE supplier_id = ?
        ORDER BY name ASC, id ASC
        """
    )
    rep_query.addBindValue(int(supplier_id))
    if not rep_query.exec():
        raise Exception(f"Failed to load supplier reps: {rep_query.lastError().text()}")

    reps = []
    while rep_query.next():
        reps.append(
            {
                "id": int(rep_query.value(0) or 0),
                "name": str(rep_query.value(1) or ""),
                "contact": str(rep_query.value(2) or ""),
            }
        )

    return {
        "supplier_id": int(supplier_query.value(0) or 0),
        "supplier_name": str(supplier_query.value(1) or ""),
        "supplier_contact": str(supplier_query.value(2) or ""),
        "supplier_address": str(supplier_query.value(3) or ""),
        "payable": float(supplier_query.value(4) or 0.0),
        "receiveable": float(supplier_query.value(5) or 0.0),
        "reps": reps,
    }


def prepare_customer_transaction_payload(
    *,
    customer_id,
    salesman_id,
    paid_amount,
    received_amount,
    note,
    payment_data,
    allow_excess=False,
):
    balance_row = _fetch_party_balance_row("customer", customer_id)
    if balance_row is None:
        raise Exception("Customer not found.")

    paid_amount = float(paid_amount or 0.0)
    received_amount = float(received_amount or 0.0)

    if paid_amount > 0 and received_amount > 0:
        raise Exception("Cannot process both Paid and Received together.")
    if paid_amount < 0 or received_amount < 0:
        raise Exception("Amounts cannot be negative.")
    if paid_amount == 0 and received_amount == 0:
        raise Exception("Enter Paid or Received amount.")

    payable_before = float(balance_row["payable"] or 0.0)
    receiveable_before = float(balance_row["receiveable"] or 0.0)
    payable_after = payable_before
    receiveable_after = receiveable_before
    due_amount = 0.0
    remaining_due = 0.0
    receiveable_now = 0.0
    remaining_now = 0.0
    paid = 0.0
    received = 0.0
    transaction_type = None

    if received_amount > 0:
        transaction_type = "RECEIPT"
        received = received_amount
        if received_amount <= receiveable_before:
            remaining_now = receiveable_before - received_amount
            receiveable_after = remaining_now
        else:
            excess = received_amount - receiveable_before
            if not allow_excess:
                return {
                    "needs_confirmation": True,
                    "title": "Excess Receipt",
                    "message": "Received exceeds receivable.\nExcess will be moved to Payable.\n\nContinue?",
                }
            remaining_now = 0.0
            receiveable_after = 0.0
            payable_after = payable_before + excess
            remaining_due = excess
    else:
        transaction_type = "REFUND"
        paid = paid_amount
        due_amount = payable_before
        if paid_amount <= payable_before:
            remaining_due = payable_before - paid_amount
            payable_after = remaining_due
        else:
            excess = paid_amount - payable_before
            if not allow_excess:
                return {
                    "needs_confirmation": True,
                    "title": "Excess Refund",
                    "message": "Refund exceeds payable.\nExcess will be moved to Receivable.\n\nContinue?",
                }
            remaining_due = 0.0
            payable_after = 0.0
            receiveable_now = excess
            remaining_now = receiveable_before + excess
            receiveable_after = receiveable_before + excess

    session_id = get_active_session_id(strict=True)
    if session_id is None:
        raise Exception("No active session found.")

    return {
        "customer": int(customer_id),
        "salesman": salesman_id,
        "transaction_type": transaction_type,
        "ref": None,
        "return_ref": None,
        "payable_before": payable_before,
        "due_amount": due_amount,
        "paid": paid,
        "remaining_due": remaining_due,
        "payable_after": payable_after,
        "receiveable_before": receiveable_before,
        "receiveable_now": receiveable_now,
        "received": received,
        "remaining_now": remaining_now,
        "receiveable_after": receiveable_after,
        "payment_method": payment_data["payment_method"],
        "bank_name": payment_data["bank_name"],
        "account_no": payment_data["account_no"],
        "transaction_mode": payment_data["transaction_mode"],
        "wallet_provider": payment_data["wallet_provider"],
        "wallet_no": payment_data["wallet_no"],
        "payment_reference": payment_data["payment_reference"],
        "note": str(note or "").strip() or None,
        "session_id": session_id,
    }


def prepare_supplier_transaction_payload(
    *,
    supplier_id,
    rep_id,
    paid_amount,
    received_amount,
    note,
    payment_data,
    allow_excess=False,
):
    balance_row = _fetch_party_balance_row("supplier", supplier_id)
    if balance_row is None:
        raise Exception("Supplier not found.")

    paid_amount = float(paid_amount or 0.0)
    received_amount = float(received_amount or 0.0)

    if paid_amount > 0 and received_amount > 0:
        raise Exception("Cannot process Payment and Receipt together.")
    if paid_amount < 0 or received_amount < 0:
        raise Exception("Amounts cannot be negative.")
    if paid_amount == 0 and received_amount == 0:
        raise Exception("Enter paid or received amount.")

    payable_before = float(balance_row["payable"] or 0.0)
    receiveable_before = float(balance_row["receiveable"] or 0.0)
    payable_after = payable_before
    receiveable_after = receiveable_before
    due_amount = 0.0
    remaining_due = 0.0
    receiveable_now = 0.0
    remaining_now = 0.0
    paid = 0.0
    received = 0.0
    transaction_type = None

    if paid_amount > 0:
        transaction_type = "PAYMENT"
        paid = paid_amount
        due_amount = payable_before
        if paid_amount <= payable_before:
            remaining_due = payable_before - paid_amount
            payable_after = remaining_due
        else:
            overpayment = paid_amount - payable_before
            remaining_due = 0.0
            payable_after = 0.0
            receiveable_now = overpayment
            remaining_now = receiveable_before + overpayment
            receiveable_after = receiveable_before + overpayment
    else:
        transaction_type = "RECEIPT"
        received = received_amount
        if received_amount <= receiveable_before:
            remaining_now = receiveable_before - received_amount
            receiveable_after = remaining_now
        else:
            excess = received_amount - receiveable_before
            if not allow_excess:
                return {
                    "needs_confirmation": True,
                    "title": "Excess Receipt",
                    "message": "Received amount exceeds receivable.\nExcess will be moved to Payable.\n\nContinue?",
                }
            remaining_now = 0.0
            receiveable_after = 0.0
            payable_after = payable_before + excess
            remaining_due = excess

    session_id = get_active_session_id(strict=True)
    if session_id is None:
        raise Exception("No active session found.")

    return {
        "supplier": int(supplier_id),
        "rep": rep_id,
        "transaction_type": transaction_type,
        "ref": None,
        "return_ref": None,
        "payable_before": payable_before,
        "due_amount": due_amount,
        "paid": paid,
        "remaining_due": remaining_due,
        "payable_after": payable_after,
        "receiveable_before": receiveable_before,
        "receiveable_now": receiveable_now,
        "received": received,
        "remaining_now": remaining_now,
        "receiveable_after": receiveable_after,
        "session_id": session_id,
        "payment_method": payment_data["payment_method"],
        "bank_name": payment_data["bank_name"],
        "account_no": payment_data["account_no"],
        "transaction_mode": payment_data["transaction_mode"],
        "wallet_provider": payment_data["wallet_provider"],
        "wallet_no": payment_data["wallet_no"],
        "payment_reference": payment_data["payment_reference"],
        "note": str(note or "").strip() or None,
    }


def save_customer_transaction_payload(data):
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
    for key in [
        "customer", "transaction_type", "ref", "return_ref",
        "payable_before", "due_amount", "paid", "remaining_due", "payable_after",
        "receiveable_before", "receiveable_now", "received", "remaining_now", "receiveable_after",
        "payment_method", "bank_name", "account_no", "transaction_mode",
        "wallet_provider", "wallet_no", "payment_reference",
        "salesman", "note", "session_id",
    ]:
        query.addBindValue(data[key])
    if not query.exec():
        raise Exception(query.lastError().text())

    update_query = _new_query()
    update_query.prepare(
        """
        UPDATE customer
        SET payable = ?, receiveable = ?
        WHERE id = ?
        """
    )
    update_query.addBindValue(data["payable_after"])
    update_query.addBindValue(data["receiveable_after"])
    update_query.addBindValue(data["customer"])
    if not update_query.exec():
        raise Exception(update_query.lastError().text())


def save_supplier_transaction_payload(data):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO supplier_transaction
        (
            supplier, transaction_type, ref, return_ref,
            payable_before, due_amount, paid, remaining_due, payable_after,
            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
            rep, note, session_id,
            payment_method, bank_name, account_no, transaction_mode,
            wallet_provider, wallet_no, payment_reference
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    for key in [
        "supplier", "transaction_type", "ref", "return_ref",
        "payable_before", "due_amount", "paid", "remaining_due", "payable_after",
        "receiveable_before", "receiveable_now", "received", "remaining_now", "receiveable_after",
        "rep", "note", "session_id",
        "payment_method", "bank_name", "account_no", "transaction_mode",
        "wallet_provider", "wallet_no", "payment_reference",
    ]:
        query.addBindValue(data[key])
    if not query.exec():
        raise Exception(query.lastError().text())

    update_query = _new_query()
    update_query.prepare(
        """
        UPDATE supplier
        SET payable = ?, receiveable = ?
        WHERE id = ?
        """
    )
    update_query.addBindValue(data["payable_after"])
    update_query.addBindValue(data["receiveable_after"])
    update_query.addBindValue(data["supplier"])
    if not update_query.exec():
        raise Exception(update_query.lastError().text())


def _fetch_party_balance_summary(party_kind):
    table_name = _party_table_name(party_kind)

    totals_query = _new_query()
    totals_query.prepare(
        f"""
        SELECT
            COALESCE(SUM(COALESCE(payable, 0)), 0),
            COALESCE(SUM(COALESCE(receiveable, 0)), 0)
        FROM {table_name}
        """
    )
    if not totals_query.exec() or not totals_query.next():
        raise Exception(f"Failed to load {party_kind} balance summary: {totals_query.lastError().text()}")

    reconciliation_query = _new_query()
    reconciliation_query.prepare(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE COALESCE(payable, 0) > 0 AND COALESCE(receiveable, 0) > 0
        """
    )
    if not reconciliation_query.exec() or not reconciliation_query.next():
        raise Exception(
            f"Failed to load {party_kind} reconciliation summary: {reconciliation_query.lastError().text()}"
        )

    return {
        "total_payable": float(totals_query.value(0) or 0.0),
        "total_receiveable": float(totals_query.value(1) or 0.0),
        "reconciliation_count": int(reconciliation_query.value(0) or 0),
    }


def _reconcile_internal_balance(party_kind, party_id):
    balance_row = _fetch_party_balance_row(party_kind, party_id)
    if balance_row is None:
        raise LookupError(f"{party_kind.title()} could not be loaded for reconciliation.")

    payable_before = float(balance_row["payable"] or 0.0)
    receiveable_before = float(balance_row["receiveable"] or 0.0)
    reconcile_amount = min(payable_before, receiveable_before)
    if reconcile_amount <= 0:
        raise ValueError(f"This {party_kind} has no balances to reconcile.")

    session_id = get_active_session_id(strict=True)
    if session_id is None:
        raise RuntimeError("Open a daily session before reconciling balances.")

    payable_after = payable_before - reconcile_amount
    receiveable_after = receiveable_before - reconcile_amount

    config = _party_reconciliation_config(party_kind)
    db = QSqlDatabase.database()
    if not db.transaction():
        raise Exception("Could not start reconciliation transaction.")

    try:
        insert_query = _new_query()
        insert_query.prepare(config["insert_sql"])
        for value in config["build_insert_values"](
            party_id=party_id,
            payable_before=payable_before,
            receiveable_before=receiveable_before,
            reconcile_amount=reconcile_amount,
            payable_after=payable_after,
            receiveable_after=receiveable_after,
            session_id=session_id,
        ):
            insert_query.addBindValue(value)

        if not insert_query.exec():
            raise Exception(insert_query.lastError().text())

        update_query = _new_query()
        update_query.prepare(config["update_sql"])
        update_query.addBindValue(payable_after)
        update_query.addBindValue(receiveable_after)
        update_query.addBindValue(party_id)

        if not update_query.exec():
            raise Exception(update_query.lastError().text())

        if not db.commit():
            raise Exception("Could not commit reconciliation.")

        return {
            "party_name": balance_row["name"],
            "reconcile_amount": reconcile_amount,
            "payable_before": payable_before,
            "receiveable_before": receiveable_before,
            "payable_after": payable_after,
            "receiveable_after": receiveable_after,
        }
    except Exception:
        db.rollback()
        raise


def _fetch_party_balance_row(party_kind, party_id):
    table_name = _party_table_name(party_kind)
    query = _new_query()
    query.prepare(
        f"""
        SELECT
            COALESCE(name, ''),
            COALESCE(payable, 0),
            COALESCE(receiveable, 0)
        FROM {table_name}
        WHERE id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(party_id))
    if not query.exec():
        raise Exception(f"Failed to load {party_kind}: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "name": str(query.value(0) or ""),
        "payable": float(query.value(1) or 0.0),
        "receiveable": float(query.value(2) or 0.0),
    }


def _party_table_name(party_kind):
    if party_kind == "customer":
        return "customer"
    if party_kind == "supplier":
        return "supplier"
    raise ValueError(f"Unsupported party kind: {party_kind}")


def _party_reconciliation_config(party_kind):
    if party_kind == "customer":
        return {
            "insert_sql": """
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
            """,
            "update_sql": """
                UPDATE customer
                SET payable = ?, receiveable = ?
                WHERE id = ?
            """,
            "build_insert_values": lambda **v: [
                v["party_id"],
                "INTERNAL_RECONCILIATION",
                None,
                None,
                v["payable_before"],
                v["reconcile_amount"],
                0.0,
                v["payable_after"],
                v["payable_after"],
                v["receiveable_before"],
                v["reconcile_amount"],
                0.0,
                v["receiveable_after"],
                v["receiveable_after"],
                "Internal",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                f"Internally reconciled {v['reconcile_amount']:.2f} against customer balance.",
                v["session_id"],
            ],
        }

    if party_kind == "supplier":
        return {
            "insert_sql": """
                INSERT INTO supplier_transaction
                (
                    supplier, transaction_type, ref, return_ref,
                    payable_before, due_amount, paid, remaining_due, payable_after,
                    receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                    rep, note, session_id,
                    payment_method, bank_name, account_no, transaction_mode,
                    wallet_provider, wallet_no, payment_reference
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            "update_sql": """
                UPDATE supplier
                SET payable = ?, receiveable = ?
                WHERE id = ?
            """,
            "build_insert_values": lambda **v: [
                v["party_id"],
                "INTERNAL_RECONCILIATION",
                None,
                None,
                v["payable_before"],
                v["reconcile_amount"],
                0.0,
                v["payable_after"],
                v["payable_after"],
                v["receiveable_before"],
                v["reconcile_amount"],
                0.0,
                v["receiveable_after"],
                v["receiveable_after"],
                None,
                f"Internally reconciled {v['reconcile_amount']:.2f} against supplier balance.",
                v["session_id"],
                "Internal",
                None,
                None,
                None,
                None,
                None,
                None,
            ],
        }

    raise ValueError(f"Unsupported party kind: {party_kind}")
