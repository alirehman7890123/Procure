import bcrypt

from PySide6.QtSql import QSqlQuery

from medic.utilities.permissions import Permissions


def _new_query():
    return QSqlQuery()


def validate_password_strength(password):
    if len(password or "") < 8:
        raise ValueError("Password must be at least 8 characters long.")


def username_exists(username, *, exclude_user_id=None):
    username = str(username or "").strip()
    if not username:
        return False

    query = _new_query()
    if exclude_user_id in (None, "", 0):
        query.prepare("SELECT COUNT(*) FROM auth WHERE username = ?")
        query.addBindValue(username)
    else:
        query.prepare("SELECT COUNT(*) FROM auth WHERE username = ? AND id != ?")
        query.addBindValue(username)
        query.addBindValue(int(exclude_user_id))

    if query.exec() and query.next():
        return int(query.value(0) or 0) > 0
    raise Exception("Error checking username.")


def validate_user_payload(*, firstname, lastname, email, username, role):
    firstname = str(firstname or "").strip()
    lastname = str(lastname or "").strip()
    email = str(email or "").strip()
    username = str(username or "").strip()
    role = str(role or "").strip()

    if not firstname:
        raise ValueError("First name is required.")
    if not username:
        raise ValueError("Username is required.")
    if role not in Permissions.known_roles():
        raise ValueError(f"Unknown role '{role}'. Please select a valid role.")
    if email and ("@" not in email or "." not in email):
        raise ValueError("Invalid email format.")

    return {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "username": username,
        "role": role,
    }


def create_user(*, firstname, lastname, email, username, password, role):
    payload = validate_user_payload(
        firstname=firstname,
        lastname=lastname,
        email=email,
        username=username,
        role=role,
    )
    validate_password_strength(password)

    if username_exists(payload["username"]):
        raise ValueError("Username already exists. Please choose another.")

    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(str(password).encode(), salt).decode()
    salt_text = salt.decode()

    auth_query = _new_query()
    auth_query.prepare(
        """
        INSERT INTO auth (firstname, lastname, email, username, password_hash, salt, role, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    auth_query.addBindValue(payload["firstname"])
    auth_query.addBindValue(payload["lastname"])
    auth_query.addBindValue(payload["email"])
    auth_query.addBindValue(payload["username"])
    auth_query.addBindValue(password_hash)
    auth_query.addBindValue(salt_text)
    auth_query.addBindValue(payload["role"])
    auth_query.addBindValue("active")

    if not auth_query.exec():
        raise Exception(auth_query.lastError().text())

    employee_query = _new_query()
    employee_query.prepare(
        """
        INSERT INTO employee (name, email, role, status)
        VALUES (?, ?, ?, ?)
        """
    )
    employee_query.addBindValue(f"{payload['firstname']} {payload['lastname']}".strip())
    employee_query.addBindValue(payload["email"])
    employee_query.addBindValue(payload["role"])
    employee_query.addBindValue("active")

    if not employee_query.exec():
        raise Exception(employee_query.lastError().text())


def fetch_user_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT id, firstname, lastname, email, username, role, status
        FROM auth
        ORDER BY id DESC
        """
    )
    if not query.exec():
        raise Exception(f"Could not load users.\n\n{query.lastError().text()}")

    rows = []
    while query.next():
        rows.append({
            "id": int(query.value(0) or 0),
            "firstname": str(query.value(1) or ""),
            "lastname": str(query.value(2) or ""),
            "email": str(query.value(3) or ""),
            "username": str(query.value(4) or ""),
            "role": str(query.value(5) or ""),
            "status": str(query.value(6) or ""),
        })
    return rows


def fetch_user_detail(user_id):
    query = _new_query()
    query.prepare(
        """
        SELECT id, firstname, lastname, email, username, role, status
        FROM auth
        WHERE id = ?
        """
    )
    query.addBindValue(int(user_id))

    if not query.exec():
        raise Exception(f"Could not load user.\n\n{query.lastError().text()}")
    if not query.next():
        return None

    return {
        "id": int(query.value(0) or 0),
        "firstname": str(query.value(1) or "-"),
        "lastname": str(query.value(2) or "-"),
        "email": str(query.value(3) or "-"),
        "username": str(query.value(4) or "-"),
        "role": str(query.value(5) or "-"),
        "status": str(query.value(6) or "-"),
    }


def fetch_profile_by_username(username):
    username = str(username or "").strip()
    if not username:
        return None

    query = _new_query()
    query.prepare(
        """
        SELECT id, firstname, lastname, email, role, status, username
        FROM auth
        WHERE username = ?
        """
    )
    query.addBindValue(username)

    if not query.exec():
        raise Exception(f"Could not load profile.\n\n{query.lastError().text()}")
    if not query.next():
        return None

    return {
        "id": int(query.value(0) or 0),
        "firstname": str(query.value(1) or ""),
        "lastname": str(query.value(2) or ""),
        "email": str(query.value(3) or ""),
        "role": str(query.value(4) or ""),
        "status": str(query.value(5) or ""),
        "username": str(query.value(6) or username),
    }


def update_user_profile(*, user_id, firstname, lastname, email, username):
    firstname = str(firstname or "").strip()
    lastname = str(lastname or "").strip()
    email = str(email or "").strip()
    username = str(username or "").strip()

    if not firstname:
        raise ValueError("First name is required.")
    if not username:
        raise ValueError("Username is required.")
    if email and ("@" not in email or "." not in email):
        raise ValueError("Invalid email format.")

    if username_exists(username, exclude_user_id=user_id):
        raise ValueError("Username already exists. Please choose another.")

    query = _new_query()
    query.prepare(
        """
        UPDATE auth
        SET firstname=?, lastname=?, email=?, username=?
        WHERE id=?
        """
    )
    query.addBindValue(firstname)
    query.addBindValue(lastname)
    query.addBindValue(email)
    query.addBindValue(username)
    query.addBindValue(int(user_id))

    if not query.exec():
        raise Exception(f"Could not update profile.\n\n{query.lastError().text()}")

    return {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "username": username,
    }


def change_user_password(*, username, current_password, new_password, confirm_password):
    username = str(username or "").strip()
    current_password = str(current_password or "")
    new_password = str(new_password or "")
    confirm_password = str(confirm_password or "")

    if not username:
        raise ValueError("User not found.")
    if not current_password or not new_password or not confirm_password:
        raise ValueError("All the fields are required.")
    if new_password != confirm_password:
        raise ValueError("New passwords do not match.")

    validate_password_strength(new_password)

    query = _new_query()
    query.prepare("SELECT id, password_hash FROM auth WHERE username = ?")
    query.addBindValue(username)

    if not query.exec() or not query.next():
        raise Exception("User not found or query failed.")

    user_id = int(query.value(0) or 0)
    stored_hash = str(query.value(1) or "")

    try:
        current_password_ok = bcrypt.checkpw(current_password.encode(), stored_hash.encode())
    except Exception:
        current_password_ok = False

    if not current_password_ok:
        raise ValueError("Current password is incorrect.")

    new_salt = bcrypt.gensalt()
    new_hash = bcrypt.hashpw(new_password.encode(), new_salt).decode()

    update_query = _new_query()
    update_query.prepare("UPDATE auth SET password_hash = ?, salt = ? WHERE id = ?")
    update_query.addBindValue(new_hash)
    update_query.addBindValue(new_salt.decode())
    update_query.addBindValue(user_id)

    if not update_query.exec():
        raise Exception(f"Could not update password.\n\n{update_query.lastError().text()}")
