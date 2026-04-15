DEFAULT_ACCOUNTING_SETTINGS = {
    "sales_discount_policy": "both",
    "global_sales_discount_group_id": None,
    "global_sales_discount_enabled": False,
    "global_sales_tax_group_id": None,
    "global_sales_tax_enabled": False,
    "theme_primary_color": "#2F5D7C",
    "theme_sidebar_color": "#151325",
    "sales_tax_policy": "both",
    "opening_inventory_value": 0.0,
}


def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


def normalize_hex_value(value, fallback):
    text = str(value or "").strip().upper()
    if len(text) == 7 and text.startswith("#"):
        hex_part = text[1:]
        if all(ch in "0123456789ABCDEF" for ch in hex_part):
            return text
    return str(fallback or "#000000").strip().upper()


def load_accounting_settings():
    query = _new_query()
    query.prepare(
        """
        SELECT
            COALESCE(sales_discount_policy, 'both'),
            global_sales_discount_group_id,
            COALESCE(global_sales_discount_enabled, 0),
            global_sales_tax_group_id,
            COALESCE(global_sales_tax_enabled, 0),
            COALESCE(theme_primary_color, '#2F5D7C'),
            COALESCE(theme_sidebar_color, '#151325'),
            COALESCE(sales_tax_policy, 'both'),
            COALESCE(opening_inventory_value, 0)
        FROM accounting_settings
        WHERE id = 1
        LIMIT 1
        """
    )
    if not query.exec() or not query.next():
        return dict(DEFAULT_ACCOUNTING_SETTINGS)

    return {
        "sales_discount_policy": str(query.value(0) or "both").strip() or "both",
        "global_sales_discount_group_id": query.value(1),
        "global_sales_discount_enabled": bool(int(query.value(2) or 0)),
        "global_sales_tax_group_id": query.value(3),
        "global_sales_tax_enabled": bool(int(query.value(4) or 0)),
        "theme_primary_color": normalize_hex_value(query.value(5), DEFAULT_ACCOUNTING_SETTINGS["theme_primary_color"]),
        "theme_sidebar_color": normalize_hex_value(query.value(6), DEFAULT_ACCOUNTING_SETTINGS["theme_sidebar_color"]),
        "sales_tax_policy": str(query.value(7) or "both").strip() or "both",
        "opening_inventory_value": float(query.value(8) or 0.0),
    }


def save_accounting_settings(overrides):
    settings = dict(DEFAULT_ACCOUNTING_SETTINGS)
    settings.update(load_accounting_settings())
    settings.update(dict(overrides or {}))

    query = _new_query()
    query.prepare(
        """
        INSERT INTO accounting_settings (
            id,
            sales_discount_policy,
            global_sales_discount_group_id,
            global_sales_discount_enabled,
            global_sales_tax_group_id,
            global_sales_tax_enabled,
            theme_primary_color,
            theme_sidebar_color,
            sales_tax_policy,
            opening_inventory_value,
            updated_at
        )
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id)
        DO UPDATE SET
            sales_discount_policy = excluded.sales_discount_policy,
            global_sales_discount_group_id = excluded.global_sales_discount_group_id,
            global_sales_discount_enabled = excluded.global_sales_discount_enabled,
            global_sales_tax_group_id = excluded.global_sales_tax_group_id,
            global_sales_tax_enabled = excluded.global_sales_tax_enabled,
            theme_primary_color = excluded.theme_primary_color,
            theme_sidebar_color = excluded.theme_sidebar_color,
            sales_tax_policy = excluded.sales_tax_policy,
            opening_inventory_value = excluded.opening_inventory_value,
            updated_at = CURRENT_TIMESTAMP
        """
    )
    query.addBindValue(settings["sales_discount_policy"])
    query.addBindValue(settings["global_sales_discount_group_id"])
    query.addBindValue(1 if settings["global_sales_discount_enabled"] else 0)
    query.addBindValue(settings["global_sales_tax_group_id"])
    query.addBindValue(1 if settings["global_sales_tax_enabled"] else 0)
    query.addBindValue(normalize_hex_value(settings["theme_primary_color"], DEFAULT_ACCOUNTING_SETTINGS["theme_primary_color"]))
    query.addBindValue(normalize_hex_value(settings["theme_sidebar_color"], DEFAULT_ACCOUNTING_SETTINGS["theme_sidebar_color"]))
    query.addBindValue(settings["sales_tax_policy"])
    query.addBindValue(float(settings["opening_inventory_value"] or 0.0))

    if not query.exec():
        raise Exception(query.lastError().text())

    return load_accounting_settings()


def load_sales_policy_settings():
    settings = load_accounting_settings()
    return {
        "discount_policy": settings["sales_discount_policy"],
        "tax_policy": settings["sales_tax_policy"],
    }


def load_sales_discount_settings():
    settings = load_accounting_settings()
    return {
        "policy": settings["sales_discount_policy"],
        "group_id": settings["global_sales_discount_group_id"],
        "enabled": settings["global_sales_discount_enabled"],
    }


def save_sales_discount_settings(*, policy, group_id, enabled):
    if enabled and group_id is None:
        raise ValueError("Select a global sales discount group before enabling the global promo.")
    return save_accounting_settings(
        {
            "sales_discount_policy": policy or "both",
            "global_sales_discount_group_id": group_id,
            "global_sales_discount_enabled": bool(enabled),
        }
    )


def load_sales_tax_settings():
    settings = load_accounting_settings()
    return {
        "policy": settings["sales_tax_policy"],
        "group_id": settings["global_sales_tax_group_id"],
        "enabled": settings["global_sales_tax_enabled"],
    }


def save_sales_tax_settings(*, policy, group_id, enabled):
    if enabled and group_id is None:
        raise ValueError("Select a global sales tax group before enabling global tax.")
    return save_accounting_settings(
        {
            "sales_tax_policy": policy or "both",
            "global_sales_tax_group_id": group_id,
            "global_sales_tax_enabled": bool(enabled),
        }
    )


def load_theme_settings():
    settings = load_accounting_settings()
    return {
        "theme_primary_color": settings["theme_primary_color"],
        "theme_sidebar_color": settings["theme_sidebar_color"],
    }


def save_theme_settings(*, primary_color, sidebar_color):
    return save_accounting_settings(
        {
            "theme_primary_color": normalize_hex_value(primary_color, DEFAULT_ACCOUNTING_SETTINGS["theme_primary_color"]),
            "theme_sidebar_color": normalize_hex_value(sidebar_color, DEFAULT_ACCOUNTING_SETTINGS["theme_sidebar_color"]),
        }
    )


def load_opening_inventory_value():
    return float(load_accounting_settings()["opening_inventory_value"] or 0.0)


def save_opening_inventory_value(value):
    try:
        numeric_value = float(value or 0.0)
    except (TypeError, ValueError):
        raise ValueError("Opening inventory value must be a valid number.")
    return save_accounting_settings({"opening_inventory_value": numeric_value})
