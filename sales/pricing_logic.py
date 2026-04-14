def compute_line_pricing(
    qty,
    rate,
    discount_text,
    discount_mode,
    tax_text,
    discount_fixed_amount=0.0,
    discount_apply_on_sale=True,
    line_discount_enabled=True,
    tax_fixed_amount=0.0,
    tax_apply_on_sale=True,
    line_tax_enabled=True,
):
    qty = float(qty or 0.0)
    rate = float(rate or 0.0)
    subtotal = qty * rate

    try:
        entered_discount_value = float(discount_text or 0.0)
    except ValueError:
        entered_discount_value = 0.0

    entered_discount_value = max(entered_discount_value, 0.0)
    if discount_mode == "amount":
        entered_discount_amount = min(entered_discount_value, subtotal)
    else:
        entered_discount_amount = subtotal * entered_discount_value / 100.0

    try:
        discount_fixed_amount = float(discount_fixed_amount or 0.0)
    except ValueError:
        discount_fixed_amount = 0.0
    discount_fixed_amount = max(discount_fixed_amount, 0.0)

    if not discount_apply_on_sale or not line_discount_enabled:
        entered_discount_amount = 0.0
        discount_fixed_amount = 0.0

    discount_amount = min(entered_discount_amount + discount_fixed_amount, subtotal)
    discount_percent = (discount_amount / subtotal * 100.0) if subtotal > 0 else 0.0

    taxable_amount = max(subtotal - discount_amount, 0.0)

    try:
        tax_percent = float(tax_text or 0.0)
    except ValueError:
        tax_percent = 0.0
    tax_percent = max(tax_percent, 0.0)

    try:
        tax_fixed_amount = float(tax_fixed_amount or 0.0)
    except ValueError:
        tax_fixed_amount = 0.0
    tax_fixed_amount = max(tax_fixed_amount, 0.0)

    if not tax_apply_on_sale or not line_tax_enabled:
        tax_percent = 0.0
        tax_fixed_amount = 0.0

    tax_amount = taxable_amount * tax_percent / 100.0 + tax_fixed_amount
    line_total = taxable_amount + tax_amount

    return {
        "subtotal": subtotal,
        "discount_percent": discount_percent,
        "discount_fixed_amount": discount_fixed_amount,
        "discount_amount": discount_amount,
        "taxable_amount": taxable_amount,
        "tax_percent": tax_percent,
        "tax_fixed_amount": tax_fixed_amount,
        "tax_amount": tax_amount,
        "line_total": line_total,
    }


def compute_header_totals(
    subtotal,
    manual_discount,
    manual_tax,
    additional_charges,
    *,
    discount_group_id=None,
    discount_percent=0.0,
    discount_fixed_amount=0.0,
    discount_apply_on_sale=False,
    discount_manual_override=False,
    header_discount_enabled=True,
    tax_group_id=None,
    tax_percent=0.0,
    tax_fixed_amount=0.0,
    tax_apply_on_sale=False,
    tax_manual_override=False,
    header_tax_enabled=True,
):
    subtotal = max(float(subtotal or 0.0), 0.0)

    if discount_group_id is not None and not discount_manual_override:
        discount = 0.0
        if header_discount_enabled and discount_apply_on_sale:
            discount = subtotal * float(discount_percent or 0.0) / 100.0 + max(float(discount_fixed_amount or 0.0), 0.0)
        discount = max(min(discount, subtotal), 0.0)
    elif not header_discount_enabled:
        discount = 0.0
    else:
        discount = max(min(float(manual_discount or 0.0), subtotal), 0.0)

    taxable = max(subtotal - discount, 0.0)

    if tax_group_id is not None and not tax_manual_override:
        tax = 0.0
        if header_tax_enabled and tax_apply_on_sale:
            tax = taxable * float(tax_percent or 0.0) / 100.0 + max(float(tax_fixed_amount or 0.0), 0.0)
        tax = max(tax, 0.0)
    elif not header_tax_enabled:
        tax = 0.0
    else:
        tax = max(float(manual_tax or 0.0), 0.0)

    additional = max(float(additional_charges or 0.0), 0.0)
    net_amount = taxable + tax
    final_amount = net_amount + additional

    return {
        "subtotal": subtotal,
        "discount": discount,
        "taxable": taxable,
        "tax": tax,
        "net_amount": net_amount,
        "additional_charges": additional,
        "final_amount": final_amount,
    }
