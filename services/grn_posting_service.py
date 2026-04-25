import re

from services.purchase_posting_service import compute_purchase_settlement
from services.purchase_items_service import normalize_expiry_text


def build_goods_receipt_payload(
    *,
    grn_number,
    po_id,
    grn_date,
    total_value,
    header_discount,
    tax_236g,
    tax_236h,
    sales_tax,
    cn_adjustment,
    taxable,
    netamount,
    session_id,
    notes="",
    status="received",
):
    header_discount = float(header_discount or 0.0)
    tax_236g = float(tax_236g or 0.0)
    tax_236h = float(tax_236h or 0.0)
    sales_tax = float(sales_tax or 0.0)

    return {
        "grn_number": str(grn_number or "").strip().upper(),
        "po_id": int(po_id),
        "grn_date": str(grn_date or "").strip(),
        "status": status,
        "total_value": float(total_value or 0.0),
        "header_discount": header_discount,
        # Keep header_tax as combined 236 tax bucket for legacy GRN views.
        "header_tax": tax_236g + tax_236h,
        "discount": 0.0,
        "tax_236g": tax_236g,
        "tax_236h": tax_236h,
        "salestax": sales_tax,
        "cn_adjustment": float(cn_adjustment or 0.0),
        "taxable": float(taxable or 0.0),
        "netamount": float(netamount or 0.0),
        "session_id": int(session_id),
        "notes": str(notes or "").strip(),
    }


def normalize_grn_receipt_line(
    *,
    row_number,
    po_line_id,
    product_id,
    qty_received,
    unit_price,
    batch_no,
    expiry_date,
    discount,
    tax,
    landing_cost,
    expiry_parser=None,
):
    qty_received = int(qty_received or 0)
    if qty_received <= 0:
        return None

    unit_price = float(unit_price or 0.0)
    discount = float(discount or 0.0)
    tax = float(tax or 0.0)
    landing_cost = float(landing_cost if landing_cost is not None else unit_price)

    expiry_value = normalize_expiry_text(expiry_date)
    if expiry_value and expiry_parser is not None:
        parsed = expiry_parser(expiry_value)
        if parsed is None:
            raise ValueError(f"Row {row_number}: Expiry must be in MM-YY format, for example 04-26.")
        expiry_value = parsed.toString("yyyy-MM-dd")

    return {
        "po_line_id": int(po_line_id or 0),
        "product_id": int(product_id or 0),
        "qty_received": qty_received,
        "unit_price": unit_price,
        "total_received": qty_received * unit_price,
        "batch_no": str(batch_no or "").strip() or None,
        "expiry_date": expiry_value or None,
        "discount": discount,
        "tax": tax,
        "landing_cost": landing_cost,
    }


def collect_grn_totals_payload(
    *,
    subtotal,
    discount,
    taxable,
    tax_236g,
    tax_236h,
    sales_tax,
    netamount,
    cn_adjustment,
    total,
):
    return {
        "subtotal": float(subtotal or 0.0),
        "discount": float(discount or 0.0),
        "taxable": float(taxable or 0.0),
        "tax_236g": float(tax_236g or 0.0),
        "tax_236h": float(tax_236h or 0.0),
        "sales_tax": float(sales_tax or 0.0),
        "netamount": float(netamount or 0.0),
        "cn_adjustment": float(cn_adjustment or 0.0),
        "total": float(total or 0.0),
    }


def collect_grn_billing_data(
    *,
    supplier_id,
    rep,
    grn_number,
    subtotal,
    discount,
    taxable,
    tax_236g,
    tax_236h,
    sales_tax,
    netamount,
    cn_adjustment,
    total,
    paid,
    remaining,
    writeoff_enabled=False,
    due_date=None,
    session_id=None,
):
    supplier_id = int(supplier_id or 0)
    if supplier_id <= 0:
        raise ValueError("Could not resolve supplier for selected PO.")

    grn_number = str(grn_number or "").strip().upper()
    if not grn_number or not re.fullmatch(r"GRN-\d+", grn_number):
        raise ValueError("GRN number is required.")

    subtotal = max(0.0, float(subtotal or 0.0))
    discount = min(max(0.0, float(discount or 0.0)), subtotal)
    taxable = max(0.0, float(taxable or 0.0))
    tax_236g = max(0.0, float(tax_236g or 0.0))
    tax_236h = max(0.0, float(tax_236h or 0.0))
    sales_tax = max(0.0, float(sales_tax or 0.0))
    netamount = max(0.0, float(netamount or 0.0))
    cn_adjustment = max(0.0, float(cn_adjustment or 0.0))
    total = max(0.0, float(total or 0.0))
    paid = max(0.0, float(paid or 0.0))
    remaining = float(remaining or 0.0)

    if total < 0:
        raise ValueError("Final amount cannot be negative.")
    if paid < 0:
        raise ValueError("Paid amount cannot be negative.")

    expected_remaining = round(total - paid, 2)
    if abs(expected_remaining - remaining) > 0.01:
        raise ValueError("Remaining amount does not match total - paid.")

    settlement = compute_purchase_settlement(
        remaining=remaining,
        writeoff_enabled=writeoff_enabled,
        due_date=due_date,
    )

    if session_id is None:
        raise ValueError("No active session found for billing.")

    return {
        "supplier": supplier_id,
        "rep": rep,
        "sellerinvoice": grn_number,
        "subtotal": subtotal,
        "discount": discount,
        "taxable": taxable,
        "tax_236g": tax_236g,
        "tax_236h": tax_236h,
        "sales_tax": sales_tax,
        "netamount": netamount,
        "cn_adjustment": cn_adjustment,
        "total": total,
        "paid": paid,
        "remaining": remaining,
        "writeoff": settlement["writeoff"],
        "payable": settlement["payable"],
        "receivable": settlement["receivable"],
        "due_date": settlement["due_date"],
        "session_id": int(session_id),
    }
