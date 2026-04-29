from PySide6.QtSql import QSqlQuery


ROLE_OPTIONS = ["pharmacist", "salesman"]


def _new_query():
    return QSqlQuery()


def employee_role_options():
    return list(ROLE_OPTIONS)


def validate_employee_payload(
    *,
    name,
    contact="",
    email="",
    address="",
    badge="",
    role="",
):
    normalized_name = str(name or "").strip()
    normalized_contact = str(contact or "").strip()
    normalized_email = str(email or "").strip()
    normalized_address = str(address or "").strip()
    normalized_badge = str(badge or "").strip()
    normalized_role = str(role or "").strip().lower()

    if not normalized_name:
        raise ValueError("Employee name cannot be empty.")
    if normalized_contact and not normalized_contact.isdigit():
        raise ValueError("Contact must contain only digits.")
    if normalized_email and ("@" not in normalized_email or "." not in normalized_email):
        raise ValueError("Invalid email format.")
    if normalized_role not in ROLE_OPTIONS:
        raise ValueError("Select a valid employee role.")

    return {
        "name": normalized_name,
        "contact": normalized_contact,
        "email": normalized_email,
        "address": normalized_address,
        "badge": normalized_badge,
        "role": normalized_role,
    }


def create_employee(
    *,
    name,
    contact="",
    email="",
    address="",
    badge="",
    role="",
):
    payload = validate_employee_payload(
        name=name,
        contact=contact,
        email=email,
        address=address,
        badge=badge,
        role=role,
    )

    query = _new_query()
    query.prepare(
        """
        INSERT INTO employee (name, contact, email, address, badge, role)
        VALUES (?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["name"])
    query.addBindValue(payload["contact"] or None)
    query.addBindValue(payload["email"] or None)
    query.addBindValue(payload["address"] or None)
    query.addBindValue(payload["badge"] or None)
    query.addBindValue(payload["role"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def fetch_employee_detail(employee_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            id,
            name,
            contact,
            email,
            address,
            badge,
            role,
            status,
            COALESCE(joining_date, creation_date) AS joined_on
        FROM employee
        WHERE id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(employee_id))

    if not query.exec():
        raise Exception(f"Failed to load employee detail: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "id": int(query.value(0) or 0),
        "name": str(query.value(1) or "-"),
        "contact": str(query.value(2) or "-"),
        "email": str(query.value(3) or "-"),
        "address": str(query.value(4) or "-"),
        "badge": str(query.value(5) or "-"),
        "role": str(query.value(6) or "-"),
        "status": str(query.value(7) or "-"),
        "joined_on": query.value(8),
    }


def fetch_employee_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT id, name, contact, role, badge, status
        FROM employee
        ORDER BY name ASC, id DESC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load employee list: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or ""),
                "contact": str(query.value(2) or ""),
                "role": str(query.value(3) or ""),
                "badge": str(query.value(4) or ""),
                "status": str(query.value(5) or ""),
            }
        )
    return rows
