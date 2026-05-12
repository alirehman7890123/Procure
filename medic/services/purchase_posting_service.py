def compute_purchase_settlement(*, remaining, writeoff_enabled=False, due_date=None):
    remaining = float(remaining or 0.0)

    settlement = {
        "writeoff": 0.0,
        "payable": 0.0,
        "receivable": 0.0,
        "due_date": None,
    }

    if remaining > 0.0:
        if writeoff_enabled:
            settlement["writeoff"] = remaining
        else:
            settlement["payable"] = remaining
            settlement["due_date"] = due_date
        return settlement

    if remaining < 0.0:
        settlement["receivable"] = abs(remaining)

    return settlement


def build_purchase_header_payload(
    *,
    supplier,
    rep,
    sellerinvoice,
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
    session_id,
    settlement,
):
    settlement = dict(settlement or {})
    return {
        "supplier": supplier,
        "rep": rep,
        "sellerinvoice": str(sellerinvoice or "").strip(),
        "subtotal": float(subtotal or 0.0),
        "discount": float(discount or 0.0),
        "taxable": float(taxable or 0.0),
        "tax_236g": float(tax_236g or 0.0),
        "tax_236h": float(tax_236h or 0.0),
        "sales_tax": float(sales_tax or 0.0),
        "netamount": float(netamount or 0.0),
        "cn_adjustment": float(cn_adjustment or 0.0),
        "total": float(total or 0.0),
        "paid": float(paid or 0.0),
        "remaining": float(remaining or 0.0),
        "writeoff": float(settlement.get("writeoff") or 0.0),
        "payable": float(settlement.get("payable") or 0.0),
        "receivable": float(settlement.get("receivable") or 0.0),
        "due_date": settlement.get("due_date"),
        "session_id": session_id,
    }


def build_supplier_transaction_payload(
    *,
    purchase_id,
    supplier_id,
    rep_id,
    session_id,
    total,
    paid,
    settlement,
    payable_before,
    receiveable_before,
    payment,
):
    settlement = dict(settlement or {})
    payment = dict(payment or {})
    payable = float(settlement.get("payable") or 0.0)
    receivable = float(settlement.get("receivable") or 0.0)

    return {
        "supplier": supplier_id,
        "transaction_type": "PURCHASE",
        "ref": purchase_id,
        "return_ref": None,
        "payable_before": float(payable_before or 0.0),
        "due_amount": float(total or 0.0),
        "paid": float(paid or 0.0),
        "remaining_due": payable,
        "payable_after": float(payable_before or 0.0) + payable,
        "receiveable_before": float(receiveable_before or 0.0),
        "receiveable_now": receivable,
        "received": float(paid or 0.0),
        "remaining_now": receivable,
        "receiveable_after": float(receiveable_before or 0.0) + receivable,
        "rep": rep_id,
        "session_id": session_id,
        "payment_method": payment.get("payment_method"),
        "bank_name": payment.get("bank_name"),
        "account_no": payment.get("account_no"),
        "transaction_mode": payment.get("transaction_mode"),
        "wallet_provider": payment.get("wallet_provider"),
        "wallet_no": payment.get("wallet_no"),
        "payment_reference": payment.get("payment_reference"),
    }
