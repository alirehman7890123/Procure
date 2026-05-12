def clean_numeric_text(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return ""

    text = text.replace(",", "")
    filtered = []
    dot_seen = False

    for index, char in enumerate(text):
        if char.isdigit():
            filtered.append(char)
        elif char == "-" and index == 0:
            filtered.append(char)
        elif char == "." and not dot_seen:
            filtered.append(char)
            dot_seen = True

    cleaned = "".join(filtered)
    if cleaned in {"", "-", ".", "-."}:
        return ""
    return cleaned


def float_or_default(value, default=0.0):
    cleaned = clean_numeric_text(value)
    if cleaned == "":
        return None if default is None else float(default)
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None if default is None else float(default)


def parse_int_field(value, field_name, row_number):
    cleaned = clean_numeric_text(value)
    if cleaned == "":
        raise ValueError(f"Row {row_number}: Invalid {field_name}.")
    try:
        return int(float(cleaned))
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: Invalid {field_name}.")


def parse_float_field(value, field_name, row_number, default=0.0):
    cleaned = clean_numeric_text(value)
    if cleaned == "":
        return float(default)
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: Invalid {field_name}.")


def normalize_sales_item_row(
    *,
    row_number,
    product_id,
    qty_text,
    rate_text,
    discount_text,
    tax_text,
    total_text,
    discount_input_mode,
    discount_percent_applied,
    discount_amount_applied,
    tax_percent_applied,
    tax_amount_applied,
    default_discount_group_id,
    default_tax_group_id,
    discount_group_id,
    tax_group_id,
    discount_source,
    tax_source,
    subtotal,
    header_discount,
    header_tax,
    additional_charges,
):
    qty = parse_int_field(qty_text, "quantity", row_number)
    rate = parse_float_field(rate_text, "rate", row_number)
    discount_display = parse_float_field(discount_text, "discount", row_number)
    tax_display = parse_float_field(tax_text, "tax", row_number)
    line_total = parse_float_field(total_text, "line total", row_number)

    discount_percent = float_or_default(discount_percent_applied, None)
    if discount_percent is None:
        discount_percent = discount_display or 0.0

    discount_amount = float_or_default(discount_amount_applied, 0.0)

    tax_percent = float_or_default(tax_percent_applied, None)
    if tax_percent is None:
        tax_percent = tax_display or 0.0

    tax_amount = float_or_default(tax_amount_applied, 0.0)

    if qty <= 0:
        raise ValueError(f"Row {row_number}: Quantity must be greater than zero.")
    if rate < 0:
        raise ValueError(f"Row {row_number}: Rate cannot be negative.")
    if discount_percent < 0 or discount_amount < 0:
        raise ValueError(f"Row {row_number}: Discount cannot be negative.")
    if tax_percent < 0 or tax_amount < 0:
        raise ValueError(f"Row {row_number}: Tax cannot be negative.")
    if line_total < 0:
        raise ValueError(f"Row {row_number}: Line total cannot be negative.")

    subtotal = max(0.0, float(subtotal or 0.0))
    header_discount = max(0.0, float(header_discount or 0.0))
    header_tax = max(0.0, float(header_tax or 0.0))
    additional_charges = max(0.0, float(additional_charges or 0.0))

    line_weight = (line_total / subtotal) if subtotal > 0 else 0.0
    line_header_discount = header_discount * line_weight
    line_header_tax = header_tax * line_weight
    line_additional_charges = additional_charges * line_weight
    effective_line_total = round(
        line_total - line_header_discount + line_header_tax + line_additional_charges,
        2,
    )

    return {
        "product_id": int(product_id),
        "qty": qty,
        "rate": rate,
        "discount_display": discount_display,
        "tax_display": tax_display,
        "discount_input_mode": str(discount_input_mode or "percent"),
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "default_discount_group_id": default_discount_group_id,
        "default_tax_group_id": default_tax_group_id,
        "discount_group_id": discount_group_id,
        "tax_group_id": tax_group_id,
        "discount_source": str(discount_source or "manual_override"),
        "tax_source": str(tax_source or "manual_override"),
        "line_total": line_total,
        "line_weight": line_weight,
        "line_header_discount": line_header_discount,
        "line_header_tax": line_header_tax,
        "line_additional_charges": line_additional_charges,
        "effective_line_total": effective_line_total,
    }


def compute_fifo_allocation_plan(batch_rows, qty_needed):
    remaining_qty = int(qty_needed or 0)
    plan = []

    for batch in batch_rows:
        if remaining_qty <= 0:
            break

        batch_id = int(batch["batch_id"])
        available = int(float_or_default(batch.get("available"), 0.0) or 0)
        raw_cost = batch.get("unit_cost")
        unit_cost = float_or_default(raw_cost, None)

        if available <= 0:
            continue

        take_qty = min(available, remaining_qty)
        line_cost = round(take_qty * unit_cost, 2) if unit_cost is not None else None

        plan.append(
            {
                "batch_id": batch_id,
                "available": available,
                "raw_cost": raw_cost,
                "unit_cost": unit_cost,
                "take_qty": take_qty,
                "line_cost": line_cost,
                "remaining_after": remaining_qty - take_qty,
                "invalid_cost": raw_cost is not None and unit_cost is None,
            }
        )
        remaining_qty -= take_qty

    return {
        "allocations": plan,
        "remaining_qty": remaining_qty,
    }
