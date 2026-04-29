from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def validate_supplier_payload(
    *,
    name,
    contact="",
    email="",
    website="",
    address="",
    registeration="",
    payable=0.0,
    receiveable=0.0,
    status=None,
):
    normalized_name = str(name or "").strip()
    normalized_contact = str(contact or "").strip()
    normalized_email = str(email or "").strip()
    normalized_website = str(website or "").strip()
    normalized_address = str(address or "").strip()
    normalized_registration = str(registeration or "").strip()
    normalized_status = None if status is None else str(status or "").strip()

    if not normalized_name:
        raise ValueError("Supplier name cannot be empty.")
    if normalized_contact and not normalized_contact.isdigit():
        raise ValueError("Contact must contain only digits.")
    if normalized_contact and len(normalized_contact) < 7:
        raise ValueError("Contact must be at least 7 digits.")
    if normalized_email and ("@" not in normalized_email or "." not in normalized_email):
        raise ValueError("Invalid email format.")

    try:
        payable_value = float(payable or 0.0)
        receiveable_value = float(receiveable or 0.0)
    except (TypeError, ValueError):
        raise ValueError("Payable and Receivable must be numbers.")

    if payable_value < 0 or receiveable_value < 0:
        raise ValueError("Payable and Receivable cannot be negative.")

    return {
        "name": normalized_name,
        "contact": normalized_contact,
        "email": normalized_email,
        "website": normalized_website,
        "address": normalized_address,
        "registeration": normalized_registration,
        "payable": payable_value,
        "receiveable": receiveable_value,
        "status": normalized_status,
    }


def create_supplier(
    *,
    name,
    contact="",
    email="",
    website="",
    address="",
    registeration="",
    payable=0.0,
    receiveable=0.0,
):
    payload = validate_supplier_payload(
        name=name,
        contact=contact,
        email=email,
        website=website,
        address=address,
        registeration=registeration,
        payable=payable,
        receiveable=receiveable,
    )

    query = _new_query()
    query.prepare(
        """
        INSERT INTO supplier (name, contact, email, website, address, reg_no, payable, receiveable)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["name"])
    query.addBindValue(payload["contact"] or None)
    query.addBindValue(payload["email"])
    query.addBindValue(payload["website"] or None)
    query.addBindValue(payload["address"] or None)
    query.addBindValue(payload["registeration"] or None)
    query.addBindValue(payload["payable"])
    query.addBindValue(payload["receiveable"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def update_supplier(
    supplier_id,
    *,
    name,
    contact="",
    email="",
    website="",
    address="",
    status="",
    registeration="",
):
    payload = validate_supplier_payload(
        name=name,
        contact=contact,
        email=email,
        website=website,
        address=address,
        registeration=registeration,
        status=status,
    )

    query = _new_query()
    query.prepare(
        """
        UPDATE supplier
        SET name = ?, contact = ?, email = ?, website = ?, address = ?, status = ?, reg_no = ?
        WHERE id = ?
        """
    )
    query.addBindValue(payload["name"])
    query.addBindValue(payload["contact"])
    query.addBindValue(payload["email"])
    query.addBindValue(payload["website"])
    query.addBindValue(payload["address"])
    query.addBindValue(payload["status"])
    query.addBindValue(payload["registeration"] or None)
    query.addBindValue(int(supplier_id))

    if not query.exec():
        raise Exception(query.lastError().text())
    if query.numRowsAffected() == 0:
        raise Exception("Supplier was not updated.")

    return True


def fetch_supplier_detail(supplier_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            name,
            contact,
            email,
            website,
            address,
            status,
            creation_date,
            reg_no,
            payable,
            receiveable
        FROM supplier
        WHERE id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(supplier_id))

    if not query.exec():
        raise Exception(f"Failed to load supplier detail: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "id": int(query.value(0) or 0),
        "name": str(query.value(1) or "-"),
        "contact": str(query.value(2) or "-"),
        "email": str(query.value(3) or "-"),
        "website": str(query.value(4) or "-"),
        "address": str(query.value(5) or "-"),
        "status": str(query.value(6) or "-"),
        "creation_date": query.value(7),
        "reg_no": str(query.value(8) or "-"),
        "payable": float(query.value(9) or 0.0),
        "receiveable": float(query.value(10) or 0.0),
    }


def fetch_supplier_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            name,
            contact,
            email,
            website,
            status
        FROM supplier
        ORDER BY name ASC, id DESC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load supplier list: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or ""),
                "contact": str(query.value(2) or ""),
                "email": str(query.value(3) or ""),
                "website": str(query.value(4) or ""),
                "status": str(query.value(5) or ""),
            }
        )
    return rows
