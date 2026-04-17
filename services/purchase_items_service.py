import re
from datetime import date


def clean_numeric_text(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return ""

    text = text.replace(",", "")
    text = re.sub(r"[^0-9.\-]", "", text)

    if text.count(".") > 1:
        first_dot = text.find(".")
        text = text[: first_dot + 1] + text[first_dot + 1 :].replace(".", "")

    if text in {"", "-", ".", "-."}:
        return ""

    return text


def normalize_expiry_text(value):
    raw = "" if value is None else str(value).strip()
    if not raw:
        return ""

    collapsed = raw.replace("_", "").replace(" ", "")
    if not collapsed or collapsed in {"-", "--"}:
        return ""

    return raw


def float_or_default(value, default=0.0):
    cleaned = clean_numeric_text(value)
    if not cleaned:
        return float(default)
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return float(default)


def parse_expiry_to_db_date(text, today=None):
    raw = normalize_expiry_text(text)
    if not raw:
        return ""

    if re.fullmatch(r"\d{2}-\d{2}", raw):
        month = int(raw[:2])
        year = 2000 + int(raw[3:5])
        if month < 1 or month > 12:
            return ""
        normalized = date(year, month, 1)
        current = today or date.today()
        current_month = date(current.year, current.month, 1)
        if normalized < current_month:
            return ""
        return normalized.strftime("%Y-%m-%d")

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw

    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", raw):
        day, month, year = raw.split("-")
        try:
            normalized = date(int(year), int(month), int(day))
            return normalized.strftime("%Y-%m-%d")
        except ValueError:
            return ""

    return ""


def compute_purchase_distribution_factor(
    *,
    line_subtotal,
    header_discount,
    header_tax_236g,
    header_tax_236h,
    header_sales_tax,
    cn_adjustment,
):
    line_subtotal = max(0.0, float(line_subtotal or 0.0))
    header_discount = min(max(0.0, float(header_discount or 0.0)), line_subtotal)
    header_tax_236g = max(0.0, float(header_tax_236g or 0.0))
    header_tax_236h = max(0.0, float(header_tax_236h or 0.0))
    header_sales_tax = max(0.0, float(header_sales_tax or 0.0))
    cn_adjustment = max(0.0, float(cn_adjustment or 0.0))

    header_adjustments = (
        -header_discount + header_tax_236g - header_tax_236h + header_sales_tax - cn_adjustment
    )
    total_with_fees = max(0.0, line_subtotal + header_adjustments)

    return {
        "line_subtotal": line_subtotal,
        "header_adjustments": header_adjustments,
        "total_with_fees": total_with_fees,
        "distribution_factor": (total_with_fees / line_subtotal) if line_subtotal > 0 else 1.0,
    }


def normalize_purchase_item_row(
    *,
    row_number,
    product_id,
    batch_text,
    expiry_text,
    qty_text,
    bonus_text,
    rate_text,
    discount_text,
    tax_text,
    total_text,
    distribution_factor,
):
    product_id = int(product_id)
    batch = str(batch_text or "").strip() or None
    expiry = parse_expiry_to_db_date(expiry_text)
    qty = float_or_default(qty_text, 0.0)
    bonus = float_or_default(bonus_text, 0.0)
    rate = float_or_default(rate_text, 0.0)
    item_discount = float_or_default(discount_text, 0.0)
    item_tax = float_or_default(tax_text, 0.0)
    item_total = float_or_default(total_text, 0.0)
    distribution_factor = float(distribution_factor or 1.0)

    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero in row {row_number}.")
    if bonus < 0:
        raise ValueError(f"Bonus cannot be negative in row {row_number}.")
    if rate < 0:
        raise ValueError(f"Rate cannot be negative in row {row_number}.")
    if item_discount < 0:
        raise ValueError(f"Discount cannot be negative in row {row_number}.")
    if item_tax < 0:
        raise ValueError(f"Tax cannot be negative in row {row_number}.")

    landing_cost = float_or_default(item_total * distribution_factor, 0.0)

    return {
        "product": product_id,
        "batch": batch,
        "expiry": expiry or None,
        "qty": qty,
        "bonus": bonus,
        "rate": rate,
        "item_discount": item_discount,
        "item_tax": item_tax,
        "item_total": item_total,
        "landing_cost": landing_cost,
    }


def build_batch_payload(*, product_id, purchase_item_id, qty, bonus, pack_size, landing_cost, batch, expiry):
    qty = float(qty or 0.0)
    bonus = float(bonus or 0.0)
    pack_size = float(pack_size or 0.0)
    received = qty + bonus

    received_qty = received * pack_size if pack_size else qty
    paid_qty = qty * pack_size if pack_size else qty
    unit_cost_per_unit = round(landing_cost / received_qty, 6) if received_qty and received_qty > 0 else landing_cost

    return {
        "batch_no": batch,
        "expiry_date": expiry,
        "product_id": int(product_id),
        "purchaseitem_id": purchase_item_id if purchase_item_id else None,
        "total_received": float_or_default(received_qty, 0.0),
        "paid_qty": float_or_default(paid_qty, 0.0),
        "quantity_remaining": float_or_default(received_qty, 0.0),
        "unit_cost": float_or_default(unit_cost_per_unit, 0.0),
        "source": "PURCHASE",
    }
