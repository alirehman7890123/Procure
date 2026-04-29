from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def _normalize_group_name(value):
    return str(value or "").strip()


def _normalize_percent_value(value, *, field_label="Percent"):
    try:
        numeric = float(value or 0.0)
    except (TypeError, ValueError):
        raise ValueError(f"{field_label} must be a valid number.")
    if numeric < 0:
        raise ValueError(f"{field_label} cannot be negative.")
    return numeric


def validate_customer_payload(
    *,
    name,
    contact="",
    email="",
    payable=0.0,
    receiveable=0.0,
    credit_limit=0.0,
    status=None,
):
    normalized_name = str(name or "").strip()
    normalized_contact = str(contact or "").strip()
    normalized_email = str(email or "").strip()
    normalized_status = None if status is None else str(status or "").strip()

    if not normalized_name:
        raise ValueError("Customer name cannot be empty.")
    if any(char.isdigit() for char in normalized_name):
        raise ValueError("Customer name cannot contain numbers.")
    if normalized_contact and not normalized_contact.isdigit():
        raise ValueError("Contact must contain only digits.")
    if normalized_email and ("@" not in normalized_email or "." not in normalized_email):
        raise ValueError("Invalid email format.")

    try:
        payable_value = float(payable or 0.0)
        receiveable_value = float(receiveable or 0.0)
        credit_limit_value = float(credit_limit or 0.0)
    except (TypeError, ValueError):
        raise ValueError("Payable, Receivable, and Credit Limit must be numbers.")

    if payable_value < 0 or receiveable_value < 0 or credit_limit_value < 0:
        raise ValueError("Payable, Receivable, and Credit Limit cannot be negative.")

    return {
        "name": normalized_name,
        "contact": normalized_contact,
        "email": normalized_email,
        "payable": payable_value,
        "receiveable": receiveable_value,
        "credit_limit": credit_limit_value,
        "status": normalized_status,
    }


def _fetch_group_options(table_name, percent_column):
    query = _new_query()
    if not query.exec(
        f"""
        SELECT id, name, {percent_column}, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1)
        FROM {table_name}
        WHERE status = 'active'
        ORDER BY name ASC
        """
    ):
        raise Exception(f"Failed to load {table_name}: {query.lastError().text()}")

    rows = []
    while query.next():
        group_id = query.value(0)
        name = str(query.value(1) or "")
        percent = float(query.value(2) or 0.0)
        fixed_amount = float(query.value(3) or 0.0)
        apply_on_sale = bool(int(query.value(4) or 0))
        rows.append(
            {
                "id": group_id,
                "label": (
                    f"{name} ({percent:.2f}% + {fixed_amount:.2f}, "
                    f"{'Sale On' if apply_on_sale else 'Sale Off'})"
                ),
            }
        )
    return rows


def fetch_discount_group_options():
    return _fetch_group_options("discount_group", "discount_percent")


def fetch_tax_group_options():
    return _fetch_group_options("tax_group", "tax_percent")


def _create_group(*, table_name, value_column, group_name, percent_value):
    normalized_name = _normalize_group_name(group_name)
    if not normalized_name:
        raise ValueError("Group name is required.")

    normalized_percent = _normalize_percent_value(percent_value)

    query = _new_query()
    query.prepare(
        f"""
        INSERT INTO {table_name} (name, {value_column}, status)
        VALUES (?, ?, 'active')
        """
    )
    query.addBindValue(normalized_name)
    query.addBindValue(normalized_percent)

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def create_discount_group(group_name, percent_value):
    return _create_group(
        table_name="discount_group",
        value_column="discount_percent",
        group_name=group_name,
        percent_value=percent_value,
    )


def create_tax_group(group_name, percent_value):
    return _create_group(
        table_name="tax_group",
        value_column="tax_percent",
        group_name=group_name,
        percent_value=percent_value,
    )


def create_customer(
    *,
    name,
    contact="",
    email="",
    payable=0.0,
    receiveable=0.0,
    credit_limit=0.0,
    discount_group_id=None,
    tax_group_id=None,
):
    payload = validate_customer_payload(
        name=name,
        contact=contact,
        email=email,
        payable=payable,
        receiveable=receiveable,
        credit_limit=credit_limit,
    )

    query = _new_query()
    query.prepare(
        """
        INSERT INTO customer (
            name, contact, email, payable, receiveable, credit_limit, discount_group_id, tax_group_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["name"])
    query.addBindValue(payload["contact"] or None)
    query.addBindValue(payload["email"])
    query.addBindValue(payload["payable"])
    query.addBindValue(payload["receiveable"])
    query.addBindValue(payload["credit_limit"])
    query.addBindValue(discount_group_id)
    query.addBindValue(tax_group_id)

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def update_customer(
    customer_id,
    *,
    name,
    contact="",
    email="",
    status="",
    credit_limit=0.0,
    discount_group_id=None,
    tax_group_id=None,
):
    payload = validate_customer_payload(
        name=name,
        contact=contact,
        email=email,
        credit_limit=credit_limit,
    )

    query = _new_query()
    query.prepare(
        """
        UPDATE customer
        SET name = ?, contact = ?, email = ?, status = ?, credit_limit = ?, discount_group_id = ?, tax_group_id = ?
        WHERE id = ?
        """
    )
    query.addBindValue(payload["name"])
    query.addBindValue(payload["contact"])
    query.addBindValue(payload["email"])
    query.addBindValue(str(status or "").strip())
    query.addBindValue(payload["credit_limit"])
    query.addBindValue(discount_group_id)
    query.addBindValue(tax_group_id)
    query.addBindValue(int(customer_id))

    if not query.exec():
        raise Exception(query.lastError().text())
    if query.numRowsAffected() == 0:
        raise Exception("Customer was not updated.")

    return True


def fetch_customer_detail(customer_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            name,
            contact,
            email,
            status,
            creation_date,
            payable,
            receiveable,
            credit_limit,
            discount_group_id,
            tax_group_id
        FROM customer
        WHERE id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(customer_id))

    if not query.exec():
        raise Exception(f"Failed to load customer detail: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "id": int(query.value(0) or 0),
        "name": str(query.value(1) or "-"),
        "contact": str(query.value(2) or "-"),
        "email": str(query.value(3) or "-"),
        "status": str(query.value(4) or "-"),
        "creation_date": query.value(5),
        "payable": float(query.value(6) or 0.0),
        "receiveable": float(query.value(7) or 0.0),
        "credit_limit": float(query.value(8) or 0.0),
        "discount_group_id": query.value(9),
        "tax_group_id": query.value(10),
    }


def fetch_customer_transaction_rows(customer_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            creation_date,
            transaction_type,
            receiveable_now,
            payable_before,
            receiveable_before,
            paid,
            received,
            payable_after,
            receiveable_after,
            payment_method,
            id
        FROM customer_transaction
        WHERE customer = ?
        ORDER BY creation_date DESC
        """
    )
    query.addBindValue(int(customer_id))

    if not query.exec():
        raise Exception(f"Failed to load customer transactions: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "creation_date": query.value(0),
                "transaction_type": str(query.value(1) or ""),
                "due_or_credit": float(query.value(2) or 0.0),
                "payable_before": float(query.value(3) or 0.0),
                "receiveable_before": float(query.value(4) or 0.0),
                "paid": float(query.value(5) or 0.0),
                "received": float(query.value(6) or 0.0),
                "payable_after": float(query.value(7) or 0.0),
                "receiveable_after": float(query.value(8) or 0.0),
                "payment_method": str(query.value(9) or "-"),
                "transaction_id": int(query.value(10) or 0),
            }
        )
    return rows


def fetch_customer_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            name,
            contact,
            email,
            status,
            payable,
            receiveable,
            credit_limit
        FROM customer
        ORDER BY name ASC, id DESC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load customer list: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or ""),
                "contact": str(query.value(2) or ""),
                "email": str(query.value(3) or ""),
                "status": str(query.value(4) or ""),
                "payable": float(query.value(5) or 0.0),
                "receiveable": float(query.value(6) or 0.0),
                "credit_limit": float(query.value(7) or 0.0),
            }
        )
    return rows
