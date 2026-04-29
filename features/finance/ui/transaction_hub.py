from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Qt

from medic.utilities.stylus import load_stylesheets


_CARD_STYLE = """
    QFrame#txCard {{
        background-color: #FFFFFF;
        border: 1px solid #D8E4ED;
        border-radius: 10px;
        border-top: 3px solid {accent};
    }}
"""

_AMOUNT_STYLE = """
    font-size: 20px;
    font-weight: 700;
    font-family: 'montserrat';
    color: {color};
    padding: 0;
    background: transparent;
    border: none;
"""

_PILL_LABEL_STYLE = """
    font-size: 11px;
    font-weight: 700;
    font-family: 'montserrat';
    color: {fg};
    background-color: {bg};
    border-radius: 4px;
    padding: 2px 8px;
    border: none;
"""

_OPEN_BTN_STYLE = """
    QPushButton {{
        color: #FFFFFF;
        background-color: {accent};
        border: 1px solid {border};
        border-radius: 6px;
        font-weight: 700;
        font-family: 'montserrat';
        font-size: 12px;
        padding: 7px 18px;
        min-height: 28px;
    }}
    QPushButton:hover {{
        background-color: {hover};
        border: 1px solid {border};
    }}
    QPushButton:pressed {{
        background-color: {pressed};
    }}
"""


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("border: none; border-top: 1px solid #ECF0F4; margin: 2px 0;")
    return line


def _build_card(accent):
    card = QFrame()
    card.setObjectName("txCard")
    card.setStyleSheet(
        _CARD_STYLE.format(accent=accent)
        + """
        QFrame#txCard > QLabel { background: transparent; border: none; padding: 0; }
    """
    )
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(22, 18, 22, 20)
    layout.setSpacing(10)
    return card, layout


class MainTransactionWidget(QWidget):
    def __init__(self, parent=None):
        self._last_reconciliation_signature = None
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)
        self.layout = root

        header_row = QHBoxLayout()
        heading = QLabel("Transactions")
        heading.setStyleSheet(
            "font-size: 22px; font-weight: 700; font-family: 'montserrat'; "
            "color: #18374D; background: transparent; border: none; padding: 0;"
        )
        sub = QLabel("Supplier & customer balance overview")
        sub.setStyleSheet(
            "font-size: 12px; font-weight: 500; font-family: 'montserrat'; "
            "color: #7A94A6; background: transparent; border: none; padding: 0;"
        )
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(heading)
        title_col.addWidget(sub)
        header_row.addLayout(title_col)
        header_row.addStretch()
        root.addLayout(header_row)
        root.addSpacing(20)

        grid = QHBoxLayout()
        grid.setSpacing(18)

        supplier_card, sc_layout = _build_card("#2F5D7C")
        sc_title_row = QHBoxLayout()
        sc_title_row.setSpacing(8)
        sc_label = QLabel("Supplier Transactions")
        sc_label.setStyleSheet(
            "font-size: 15px; font-weight: 700; font-family: 'montserrat'; color: #18374D;"
        )
        sc_badge = QLabel("Suppliers")
        sc_badge.setStyleSheet(_PILL_LABEL_STYLE.format(fg="#2F5D7C", bg="#E4EEF5"))
        sc_title_row.addWidget(sc_label)
        sc_title_row.addStretch()
        sc_title_row.addWidget(sc_badge)
        sc_layout.addLayout(sc_title_row)
        sc_layout.addWidget(_divider())

        sp_amount_row = QHBoxLayout()
        sp_lbl = QLabel("Payable")
        sp_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #4A6070; font-family: 'montserrat';")
        self.supplier_payable_amount = QLabel("0.00")
        self.supplier_payable_amount.setStyleSheet(_AMOUNT_STYLE.format(color="#D94F4F"))
        self.supplier_payable_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sp_amount_row.addWidget(sp_lbl, 1)
        sp_amount_row.addWidget(self.supplier_payable_amount, 1)
        sc_layout.addLayout(sp_amount_row)

        sr_amount_row = QHBoxLayout()
        sr_lbl = QLabel("Receivable")
        sr_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #4A6070; font-family: 'montserrat';")
        self.supplier_receiveable_amount = QLabel("0.00")
        self.supplier_receiveable_amount.setStyleSheet(_AMOUNT_STYLE.format(color="#2A8A5A"))
        self.supplier_receiveable_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sr_amount_row.addWidget(sr_lbl, 1)
        sr_amount_row.addWidget(self.supplier_receiveable_amount, 1)
        sc_layout.addLayout(sr_amount_row)

        sc_layout.addSpacing(6)

        self.supplier_transactions_button = QPushButton("Open Supplier Transactions →")
        self.supplier_transactions_button.setCursor(Qt.PointingHandCursor)
        self.supplier_transactions_button.setStyleSheet(
            _OPEN_BTN_STYLE.format(
                accent="#2F5D7C", border="#2a506b", hover="#244A62", pressed="#163B5C"
            )
        )
        sc_layout.addWidget(self.supplier_transactions_button)

        self.supplier_reconcile_notice = QLabel("")
        self.supplier_reconcile_notice.setWordWrap(True)
        self.supplier_reconcile_notice.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #2F5D7C; "
            "background: #EAF2F8; border-radius: 4px; padding: 6px 10px; border: none;"
        )
        self.supplier_reconcile_notice.hide()
        sc_layout.addWidget(self.supplier_reconcile_notice)

        customer_card, cc_layout = _build_card("#1E7A5E")
        cc_title_row = QHBoxLayout()
        cc_title_row.setSpacing(8)
        cc_label = QLabel("Customer Transactions")
        cc_label.setStyleSheet(
            "font-size: 15px; font-weight: 700; font-family: 'montserrat'; color: #18374D;"
        )
        cc_badge = QLabel("Customers")
        cc_badge.setStyleSheet(_PILL_LABEL_STYLE.format(fg="#1E7A5E", bg="#E2F4EE"))
        cc_title_row.addWidget(cc_label)
        cc_title_row.addStretch()
        cc_title_row.addWidget(cc_badge)
        cc_layout.addLayout(cc_title_row)
        cc_layout.addWidget(_divider())

        cp_amount_row = QHBoxLayout()
        cp_lbl = QLabel("Payable")
        cp_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #4A6070; font-family: 'montserrat';")
        self.customer_payable_amount = QLabel("0.00")
        self.customer_payable_amount.setStyleSheet(_AMOUNT_STYLE.format(color="#D94F4F"))
        self.customer_payable_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cp_amount_row.addWidget(cp_lbl, 1)
        cp_amount_row.addWidget(self.customer_payable_amount, 1)
        cc_layout.addLayout(cp_amount_row)

        cr_amount_row = QHBoxLayout()
        cr_lbl = QLabel("Receivable")
        cr_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #4A6070; font-family: 'montserrat';")
        self.customer_receiveable_amount = QLabel("0.00")
        self.customer_receiveable_amount.setStyleSheet(_AMOUNT_STYLE.format(color="#2A8A5A"))
        self.customer_receiveable_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cr_amount_row.addWidget(cr_lbl, 1)
        cr_amount_row.addWidget(self.customer_receiveable_amount, 1)
        cc_layout.addLayout(cr_amount_row)

        cc_layout.addSpacing(6)

        self.customer_transactions_button = QPushButton("Open Customer Transactions →")
        self.customer_transactions_button.setCursor(Qt.PointingHandCursor)
        self.customer_transactions_button.setStyleSheet(
            _OPEN_BTN_STYLE.format(
                accent="#1E7A5E", border="#185F4A", hover="#186650", pressed="#0F4D3B"
            )
        )
        cc_layout.addWidget(self.customer_transactions_button)

        self.customer_reconcile_notice = QLabel("")
        self.customer_reconcile_notice.setWordWrap(True)
        self.customer_reconcile_notice.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #1E7A5E; "
            "background: #E2F4EE; border-radius: 4px; padding: 6px 10px; border: none;"
        )
        self.customer_reconcile_notice.hide()
        cc_layout.addWidget(self.customer_reconcile_notice)

        grid.addWidget(supplier_card)
        grid.addWidget(customer_card)
        root.addLayout(grid)
        root.addStretch()

        self.setStyleSheet(load_stylesheets())
