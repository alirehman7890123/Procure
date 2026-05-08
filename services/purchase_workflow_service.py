from medic.services.db_transaction_service import run_in_transaction
from medic.services.purchase_items_service import build_batch_payload
from medic.services.purchase_posting_service import (
    build_purchase_header_payload,
    build_supplier_transaction_payload,
)
from medic.services.purchase_transaction_service import (
    fetch_product_pack_size,
    fetch_supplier_balances,
    insert_batch_record,
    insert_purchase_header,
    insert_purchase_item,
    insert_supplier_transaction,
    mark_product_used,
    update_supplier_balances,
)


def save_purchase_invoice(*, purchase_data, item_rows, payment_data):
    normalized_rows = [dict(row) for row in list(item_rows or []) if row is not None]
    if not normalized_rows:
        raise ValueError("No valid purchase items were found to save.")

    normalized_purchase_data = dict(purchase_data or {})
    normalized_payment = dict(payment_data or {})

    def _work():
        header_payload = build_purchase_header_payload(
            supplier=int(normalized_purchase_data.get("supplier") or 0),
            rep=int(normalized_purchase_data["rep"]) if normalized_purchase_data.get("rep") not in (None, "") else None,
            sellerinvoice=str(normalized_purchase_data.get("sellerinvoice") or "").strip(),
            subtotal=float(normalized_purchase_data.get("subtotal") or 0.0),
            discount=float(normalized_purchase_data.get("discount") or 0.0),
            taxable=float(normalized_purchase_data.get("taxable") or 0.0),
            tax_236g=float(normalized_purchase_data.get("tax_236g") or 0.0),
            tax_236h=float(normalized_purchase_data.get("tax_236h") or 0.0),
            sales_tax=float(normalized_purchase_data.get("sales_tax") or 0.0),
            netamount=float(normalized_purchase_data.get("netamount") or 0.0),
            cn_adjustment=float(normalized_purchase_data.get("cn_adjustment") or 0.0),
            total=float(normalized_purchase_data.get("total") or 0.0),
            paid=float(normalized_purchase_data.get("paid") or 0.0),
            remaining=float(normalized_purchase_data.get("remaining") or 0.0),
            session_id=int(normalized_purchase_data.get("session_id") or 0),
            settlement={
                "writeoff": float(normalized_purchase_data.get("writeoff") or 0.0),
                "payable": float(normalized_purchase_data.get("payable") or 0.0),
                "receivable": float(normalized_purchase_data.get("receivable") or 0.0),
                "due_date": normalized_purchase_data.get("due_date"),
            },
        )
        purchase_id = insert_purchase_header(header_payload)

        saved_rows = 0
        for row_number, row in enumerate(normalized_rows, start=1):
            purchase_item_id = insert_purchase_item(purchase_id, row)

            pack_size = fetch_product_pack_size(row["product"])
            batch_payload = build_batch_payload(
                product_id=row["product"],
                purchase_item_id=purchase_item_id,
                qty=row["qty"],
                bonus=row["bonus"],
                pack_size=pack_size,
                landing_cost=row["landing_cost"],
                batch=row["batch"],
                expiry=row["expiry"],
            )
            insert_batch_record(batch_payload)
            mark_product_used(row["product"])
            saved_rows += 1

        if saved_rows == 0:
            raise ValueError("No valid purchase items were found to save.")

        supplier_id = int(normalized_purchase_data.get("supplier") or 0)
        rep_id = int(normalized_purchase_data["rep"]) if normalized_purchase_data.get("rep") not in (None, "") else None
        session_id = int(normalized_purchase_data.get("session_id") or 0)
        total = float(normalized_purchase_data.get("total") or 0.0)
        paid = float(normalized_purchase_data.get("paid") or 0.0)
        payable = float(normalized_purchase_data.get("payable") or 0.0)
        receivable = float(normalized_purchase_data.get("receivable") or 0.0)

        balances = fetch_supplier_balances(supplier_id)
        supplier_txn_payload = build_supplier_transaction_payload(
            purchase_id=purchase_id,
            supplier_id=supplier_id,
            rep_id=rep_id,
            session_id=session_id,
            total=total,
            paid=paid,
            settlement={"payable": payable, "receivable": receivable},
            payable_before=balances["payable_before"],
            receiveable_before=balances["receiveable_before"],
            payment=normalized_payment,
        )
        insert_supplier_transaction(supplier_txn_payload)
        update_supplier_balances(
            supplier_id,
            payable_after=supplier_txn_payload["payable_after"],
            receiveable_after=supplier_txn_payload["receiveable_after"],
        )

        return {
            "purchase_id": int(purchase_id),
            "saved_rows": saved_rows,
        }

    return run_in_transaction(
        _work,
        start_error_message="Could not start database transaction.",
        commit_error_message="Could not commit the purchase transaction.",
    )
