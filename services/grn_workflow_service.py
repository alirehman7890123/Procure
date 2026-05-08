from medic.services.db_transaction_service import run_in_transaction
from medic.services.grn_transaction_service import (
    insert_goods_receipt_header,
    insert_goods_receipt_line,
    recompute_po_status_from_receipts,
    update_goods_receipt_status,
)
from medic.services.inventory_movement_service import insert_batch_record
from medic.services.purchase_posting_service import (
    build_purchase_header_payload,
    build_supplier_transaction_payload,
)
from medic.services.purchase_transaction_service import (
    fetch_product_pack_size,
    fetch_supplier_balances,
    insert_purchase_header,
    insert_purchase_item,
    insert_supplier_transaction,
    mark_product_used,
    update_supplier_balances,
)


def save_grn_entry(*, grn_payload, receipt_rows, totals_payload, billing_data, payment_data):
    normalized_grn_payload = dict(grn_payload or {})
    normalized_receipt_rows = [dict(row) for row in list(receipt_rows or []) if row is not None]
    normalized_totals = dict(totals_payload or {})
    normalized_billing = dict(billing_data or {})
    normalized_payment = dict(payment_data or {})

    if not normalized_receipt_rows:
        raise ValueError("At least one line must have received quantity > 0.")

    def _work():
        grn_id = insert_goods_receipt_header(normalized_grn_payload)

        persisted_receipt_rows = []
        for row in normalized_receipt_rows:
            insert_goods_receipt_line(grn_id, row)
            persisted_receipt_rows.append(dict(row))

        if not persisted_receipt_rows:
            raise ValueError("At least one line must have received quantity > 0.")

        supplier_id = int(normalized_billing.get("supplier") or 0)
        rep_id = normalized_billing.get("rep")
        total_value = float(normalized_totals.get("total") or 0.0)
        paid = float(normalized_billing.get("paid") or 0.0)
        payable = float(normalized_billing.get("payable") or 0.0)
        receivable = float(normalized_billing.get("receivable") or 0.0)
        session_id = int(normalized_billing.get("session_id") or 0)
        grn_number = str(normalized_grn_payload.get("grn_number") or "").strip().upper()
        po_id = int(normalized_grn_payload.get("po_id") or 0)

        purchase_header_payload = build_purchase_header_payload(
            supplier=supplier_id,
            rep=rep_id,
            sellerinvoice=grn_number,
            subtotal=float(normalized_totals.get("subtotal") or 0.0),
            discount=float(normalized_totals.get("discount") or 0.0),
            taxable=float(normalized_totals.get("taxable") or 0.0),
            tax_236g=float(normalized_totals.get("tax_236g") or 0.0),
            tax_236h=float(normalized_totals.get("tax_236h") or 0.0),
            sales_tax=float(normalized_totals.get("sales_tax") or 0.0),
            netamount=float(normalized_totals.get("netamount") or 0.0),
            cn_adjustment=float(normalized_totals.get("cn_adjustment") or 0.0),
            total=total_value,
            paid=paid,
            remaining=float(normalized_billing.get("remaining") or 0.0),
            session_id=session_id,
            settlement={
                "writeoff": float(normalized_billing.get("writeoff") or 0.0),
                "payable": payable,
                "receivable": receivable,
                "due_date": normalized_billing.get("due_date"),
            },
        )
        purchase_id = insert_purchase_header(purchase_header_payload)

        item_rows = 0
        for row in persisted_receipt_rows:
            product_id = int(row.get("product_id") or 0)
            qty_received = float(row.get("qty_received") or 0.0)
            if product_id <= 0 or qty_received <= 0:
                continue

            unit_price = float(row.get("unit_price") or 0.0)
            discount = float(row.get("discount") or 0.0)
            tax = float(row.get("tax") or 0.0)
            landing_cost = float(row.get("landing_cost") or unit_price)
            line_total = (qty_received * unit_price) - discount + tax

            purchase_item_id = insert_purchase_item(
                purchase_id,
                {
                    "product": product_id,
                    "qty": qty_received,
                    "bonus": 0,
                    "rate": unit_price,
                    "item_discount": discount,
                    "item_tax": tax,
                    "item_total": line_total,
                    "landing_cost": landing_cost,
                },
            )
            row["purchaseitem_id"] = purchase_item_id
            item_rows += 1

        if item_rows == 0:
            raise ValueError("Purchase bill creation failed: no bill items were created.")

        balances = fetch_supplier_balances(supplier_id)
        supplier_txn_payload = build_supplier_transaction_payload(
            purchase_id=purchase_id,
            supplier_id=supplier_id,
            rep_id=rep_id,
            session_id=session_id,
            total=total_value,
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
        update_goods_receipt_status(grn_number, "billed")

        stock_batch_count = 0
        for row in persisted_receipt_rows:
            product_id = int(row.get("product_id") or 0)
            qty_received = int(row.get("qty_received") or 0)
            unit_price = float(row.get("unit_price") or 0.0)
            landing_cost = float(row.get("landing_cost") or unit_price)
            purchaseitem_id = row.get("purchaseitem_id")
            batch_no = row.get("batch_no") or None
            expiry_date = row.get("expiry_date") or None

            if product_id <= 0 or qty_received <= 0:
                continue

            try:
                pack_size = int(fetch_product_pack_size(product_id) or 1)
            except Exception:
                pack_size = 1
            if pack_size <= 0:
                pack_size = 1

            total_received_units = int(qty_received * pack_size)
            landing_cost_per_unit = round(
                landing_cost / (qty_received * pack_size), 6
            ) if qty_received > 0 and pack_size > 0 else 0.0

            insert_batch_record(
                {
                    "batch_no": batch_no,
                    "expiry_date": expiry_date,
                    "product_id": product_id,
                    "purchaseitem_id": purchaseitem_id if purchaseitem_id else None,
                    "total_received": total_received_units,
                    "paid_qty": total_received_units,
                    "quantity_remaining": total_received_units,
                    "unit_cost": landing_cost_per_unit,
                    "source": "PURCHASE",
                }
            )
            mark_product_used(product_id)
            stock_batch_count += 1

        if stock_batch_count <= 0:
            raise ValueError("Stock posting failed: no batch rows were created.")

        po_status = recompute_po_status_from_receipts(po_id)

        return {
            "grn_id": int(grn_id),
            "purchase_bill_id": int(purchase_id),
            "line_count": len(persisted_receipt_rows),
            "stock_batch_count": stock_batch_count,
            "po_status": po_status,
        }

    return run_in_transaction(
        _work,
        start_error_message="Could not start transaction.",
        commit_error_message="Could not commit GRN transaction.",
    )
