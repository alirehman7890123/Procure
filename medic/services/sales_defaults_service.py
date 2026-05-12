from PySide6.QtSql import QSqlQuery

from medic.services.accounting_settings_service import (
    load_sales_policy_settings as load_sales_policy_settings_from_accounting,
)


def load_sales_policy_settings():
    return load_sales_policy_settings_from_accounting()


def load_global_discount_settings():
    query = QSqlQuery()
    query.prepare(
        """
        SELECT
            COALESCE(a.global_sales_discount_enabled, 0),
            a.global_sales_discount_group_id,
            dg.id,
            COALESCE(dg.name, ''),
            COALESCE(dg.discount_percent, 0),
            COALESCE(dg.fixed_amount, 0),
            COALESCE(dg.apply_on_sale, 1)
        FROM accounting_settings a
        LEFT JOIN discount_group dg ON dg.id = a.global_sales_discount_group_id
        WHERE a.id = 1
        LIMIT 1
        """
    )
    if not query.exec() or not query.next():
        return {
            "state": "missing_settings",
            "data": None,
        }

    enabled = bool(int(query.value(0) or 0))
    selected_group_id = query.value(1)
    resolved_group_id = query.value(2)

    if not enabled:
        return {
            "state": "disabled",
            "selected_group_id": selected_group_id,
            "data": None,
        }

    if selected_group_id in (None, ""):
        return {
            "state": "enabled_without_selection",
            "selected_group_id": selected_group_id,
            "data": None,
        }

    if resolved_group_id in (None, ""):
        return {
            "state": "group_unresolved",
            "selected_group_id": selected_group_id,
            "data": None,
        }

    return {
        "state": "ok",
        "selected_group_id": selected_group_id,
        "data": {
            "group_id": resolved_group_id,
            "name": str(query.value(3) or ""),
            "percent": float(query.value(4) or 0.0),
            "fixed_amount": float(query.value(5) or 0.0),
            "apply_on_sale": bool(int(query.value(6) or 0)),
        },
    }


def load_global_tax_settings():
    query = QSqlQuery()
    query.prepare(
        """
        SELECT
            COALESCE(a.global_sales_tax_enabled, 0),
            a.global_sales_tax_group_id,
            tg.id,
            COALESCE(tg.name, ''),
            COALESCE(tg.tax_percent, 0),
            COALESCE(tg.fixed_amount, 0),
            COALESCE(tg.apply_on_sale, 1)
        FROM accounting_settings a
        LEFT JOIN tax_group tg ON tg.id = a.global_sales_tax_group_id
        WHERE a.id = 1
        LIMIT 1
        """
    )
    if not query.exec() or not query.next():
        return {
            "state": "missing_settings",
            "data": None,
        }

    enabled = bool(int(query.value(0) or 0))
    selected_group_id = query.value(1)
    resolved_group_id = query.value(2)

    if not enabled:
        return {
            "state": "disabled",
            "selected_group_id": selected_group_id,
            "data": None,
        }

    if selected_group_id in (None, ""):
        return {
            "state": "enabled_without_selection",
            "selected_group_id": selected_group_id,
            "data": None,
        }

    if resolved_group_id in (None, ""):
        return {
            "state": "group_unresolved",
            "selected_group_id": selected_group_id,
            "data": None,
        }

    return {
        "state": "ok",
        "selected_group_id": selected_group_id,
        "data": {
            "group_id": resolved_group_id,
            "name": str(query.value(3) or ""),
            "percent": float(query.value(4) or 0.0),
            "fixed_amount": float(query.value(5) or 0.0),
            "apply_on_sale": bool(int(query.value(6) or 0)),
        },
    }


def load_customer_header_pricing(customer_id):
    if customer_id is None:
        return None

    query = QSqlQuery()
    query.prepare(
        """
        SELECT
            dg.id,
            COALESCE(dg.name, ''),
            COALESCE(dg.discount_percent, 0),
            COALESCE(dg.fixed_amount, 0),
            COALESCE(dg.apply_on_sale, 1),
            tg.id,
            COALESCE(tg.name, ''),
            CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END,
            COALESCE(tg.fixed_amount, 0),
            COALESCE(tg.apply_on_sale, 1)
        FROM customer c
        LEFT JOIN discount_group dg ON dg.id = c.discount_group_id
        LEFT JOIN tax_group tg ON tg.id = c.tax_group_id
        WHERE c.id = ?
        """
    )
    query.addBindValue(customer_id)

    if not query.exec() or not query.next():
        return None

    return {
        "discount": {
            "group_id": query.value(0),
            "name": str(query.value(1) or ""),
            "percent": float(query.value(2) or 0.0),
            "fixed_amount": float(query.value(3) or 0.0),
            "apply_on_sale": bool(int(query.value(4) or 0)),
        },
        "tax": {
            "group_id": query.value(5),
            "name": str(query.value(6) or ""),
            "percent": float(query.value(7) or 0.0),
            "fixed_amount": float(query.value(8) or 0.0),
            "apply_on_sale": bool(int(query.value(9) or 0)),
        },
    }


def resolve_sales_header_pricing(customer_id):
    policies = load_sales_policy_settings()
    global_discount = load_global_discount_settings()
    global_tax = load_global_tax_settings()
    customer_pricing = load_customer_header_pricing(customer_id)

    resolved = {
        "policies": policies,
        "discount": {
            "group_id": None,
            "name": "",
            "percent": 0.0,
            "fixed_amount": 0.0,
            "apply_on_sale": False,
            "source": "none",
        },
        "tax": {
            "group_id": None,
            "name": "",
            "percent": 0.0,
            "fixed_amount": 0.0,
            "apply_on_sale": False,
            "source": "none",
        },
        "global_discount_meta": global_discount,
        "global_tax_meta": global_tax,
    }

    if global_discount["data"]:
        discount = global_discount["data"]
        resolved["discount"] = {
            "group_id": discount["group_id"],
            "name": discount["name"],
            "percent": discount["percent"],
            "fixed_amount": discount["fixed_amount"],
            "apply_on_sale": discount["apply_on_sale"],
            "source": "global_promo",
        }
    elif customer_pricing:
        discount = customer_pricing["discount"]
        if discount["group_id"] is not None:
            resolved["discount"] = {
                "group_id": discount["group_id"],
                "name": discount["name"],
                "percent": discount["percent"],
                "fixed_amount": discount["fixed_amount"],
                "apply_on_sale": discount["apply_on_sale"],
                "source": "customer_default",
            }

    if global_tax["data"]:
        tax = global_tax["data"]
        resolved["tax"] = {
            "group_id": tax["group_id"],
            "name": tax["name"],
            "percent": tax["percent"],
            "fixed_amount": tax["fixed_amount"],
            "apply_on_sale": tax["apply_on_sale"],
            "source": "global_tax",
        }
    elif customer_pricing:
        tax = customer_pricing["tax"]
        if tax["group_id"] is not None:
            resolved["tax"] = {
                "group_id": tax["group_id"],
                "name": tax["name"],
                "percent": tax["percent"],
                "fixed_amount": tax["fixed_amount"],
                "apply_on_sale": tax["apply_on_sale"],
                "source": "customer_default",
            }

    return resolved
