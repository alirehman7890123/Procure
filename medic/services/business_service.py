from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def fetch_business_profile():
    query = _new_query()
    query.prepare(
        """
        SELECT id, businessname, address, contact, email, website, license, ntn
        FROM business
        ORDER BY id ASC
        LIMIT 1
        """
    )

    if not query.exec():
        raise Exception(f"Could not load business data.\n\n{query.lastError().text()}")
    if not query.next():
        return None

    return {
        "id": int(query.value(0) or 0),
        "businessname": str(query.value(1) or ""),
        "address": str(query.value(2) or ""),
        "contact": str(query.value(3) or ""),
        "email": str(query.value(4) or ""),
        "website": str(query.value(5) or ""),
        "license": str(query.value(6) or ""),
        "ntn": str(query.value(7) or ""),
    }


def fetch_business_name():
    profile = fetch_business_profile()
    if not profile:
        return False
    return str(profile.get("businessname") or "")


def update_business_profile(*, business_id, businessname, address, contact, email, website, license_no, ntn):
    if business_id in (None, "", 0):
        raise ValueError("No business loaded.")

    businessname = str(businessname or "").strip()
    address = str(address or "").strip()
    contact = str(contact or "").strip()
    email = str(email or "").strip()
    website = str(website or "").strip()
    license_no = str(license_no or "").strip()
    ntn = str(ntn or "").strip()

    if not businessname:
        raise ValueError("Business name is required.")
    if email and ("@" not in email or "." not in email):
        raise ValueError("Invalid email format.")

    query = _new_query()
    query.prepare(
        """
        UPDATE business
        SET businessname=?, address=?, contact=?, email=?, website=?, license=?, ntn=?
        WHERE id=?
        """
    )
    query.addBindValue(businessname)
    query.addBindValue(address)
    query.addBindValue(contact)
    query.addBindValue(email)
    query.addBindValue(website)
    query.addBindValue(license_no)
    query.addBindValue(ntn)
    query.addBindValue(int(business_id))

    if not query.exec():
        raise Exception(f"Could not update business.\n\n{query.lastError().text()}")

    return {
        "businessname": businessname,
        "address": address,
        "contact": contact,
        "email": email,
        "website": website,
        "license": license_no,
        "ntn": ntn,
    }
