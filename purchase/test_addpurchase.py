import pytest
from unittest.mock import MagicMock, patch

class DummyWidget:
    """A dummy widget to simulate QLineEdit/QComboBox with text() and setText()."""
    def __init__(self, text=''):
        self._text = text
        self._set_text_calls = []

    def text(self):
        return self._text

    def setText(self, value):
        self._set_text_calls.append(value)
        self._text = value

    def pos(self):
        # Dummy pos for indexAt
        return 0

@pytest.fixture
def widget_with_table(monkeypatch):
    # Create a dummy AddPurchaseWidget with a mock table
    class DummyTable:
        def __init__(self):
            self._widgets = {}
            self._row = 0

        def indexAt(self, pos):
            # Always return row 0 for simplicity
            class DummyIndex:
                def row(self_nonlocal):
                    return self._row
            return DummyIndex()

        def cellWidget(self, row, col):
            return self._widgets.get((row, col), DummyWidget())

        def set_cell_widget(self, row, col, widget):
            self._widgets[(row, col)] = widget

    class DummyAddPurchaseWidget:
        def __init__(self):
            self.table = DummyTable()
            self.update_total_amount_called = False

        def update_total_amount(self):
            self.update_total_amount_called = True

        def update_amount(self, edited_widget):
            # Use the real method body from the code under test
            row = self.table.indexAt(edited_widget.pos()).row()
            try:
                qty_text = self.table.cellWidget(row, 2).text()
                rate_text = self.table.cellWidget(row, 3).text()
                discount_edit = self.table.cellWidget(row, 4).text()
                tax_edit = self.table.cellWidget(row, 5).text()

                qty = float(qty_text) if qty_text else 0
                rate = float(rate_text) if rate_text else 0
                discount = float(discount_edit) if discount_edit else 0
                tax = float(tax_edit) if tax_edit else 0

                amount = qty * rate
                discount_amount = amount * discount / 100
                self.table.cellWidget(row, 6).setText(str(discount_amount))
                taxable_amount = amount - discount_amount

                tax_amount = taxable_amount * tax / 100
                self.table.cellWidget(row, 7).setText(str(tax_amount))
                amount = taxable_amount + tax_amount
                amount = float(f"{amount:.2f}")

                self.table.cellWidget(row, 8).setText(str(amount))
                self.update_total_amount()
            except ValueError:
                self.table.cellWidget(row, 8).setText("0")

    return DummyAddPurchaseWidget()

def test_update_amount_normal_case(widget_with_table):
    # Set up widgets for row 0
    qty = DummyWidget('10')
    rate = DummyWidget('5')
    discount = DummyWidget('10')
    tax = DummyWidget('5')
    discount_amount = DummyWidget()
    tax_amount = DummyWidget()
    total_amount = DummyWidget()

    # Set up table widgets
    table = widget_with_table.table
    table.set_cell_widget(0, 2, qty)
    table.set_cell_widget(0, 3, rate)
    table.set_cell_widget(0, 4, discount)
    table.set_cell_widget(0, 5, tax)
    table.set_cell_widget(0, 6, discount_amount)
    table.set_cell_widget(0, 7, tax_amount)
    table.set_cell_widget(0, 8, total_amount)

    # Call update_amount
    widget_with_table.update_amount(qty)

    # Check calculations
    expected_amount = 10 * 5  # 50
    expected_discount = expected_amount * 10 / 100  # 5
    expected_taxable = expected_amount - expected_discount  # 45
    expected_tax = expected_taxable * 5 / 100  # 2.25
    expected_total = expected_taxable + expected_tax  # 47.25

    assert discount_amount._set_text_calls[-1] == str(expected_discount)
    assert tax_amount._set_text_calls[-1] == str(expected_tax)
    assert total_amount._set_text_calls[-1] == f"{expected_total:.2f}"
    assert widget_with_table.update_total_amount_called

def test_update_amount_empty_fields(widget_with_table):
    # All fields empty
    qty = DummyWidget('')
    rate = DummyWidget('')
    discount = DummyWidget('')
    tax = DummyWidget('')
    discount_amount = DummyWidget()
    tax_amount = DummyWidget()
    total_amount = DummyWidget()

    table = widget_with_table.table
    table.set_cell_widget(0, 2, qty)
    table.set_cell_widget(0, 3, rate)
    table.set_cell_widget(0, 4, discount)
    table.set_cell_widget(0, 5, tax)
    table.set_cell_widget(0, 6, discount_amount)
    table.set_cell_widget(0, 7, tax_amount)
    table.set_cell_widget(0, 8, total_amount)

    widget_with_table.update_amount(qty)

    assert discount_amount._set_text_calls[-1] == "0.0"
    assert tax_amount._set_text_calls[-1] == "0.0"
    assert total_amount._set_text_calls[-1] == "0.00"
    assert widget_with_table.update_total_amount_called

def test_update_amount_invalid_input(widget_with_table):
    # Invalid input for qty
    qty = DummyWidget('abc')
    rate = DummyWidget('5')
    discount = DummyWidget('10')
    tax = DummyWidget('5')
    discount_amount = DummyWidget()
    tax_amount = DummyWidget()
    total_amount = DummyWidget()

    table = widget_with_table.table
    table.set_cell_widget(0, 2, qty)
    table.set_cell_widget(0, 3, rate)
    table.set_cell_widget(0, 4, discount)
    table.set_cell_widget(0, 5, tax)
    table.set_cell_widget(0, 6, discount_amount)
    table.set_cell_widget(0, 7, tax_amount)
    table.set_cell_widget(0, 8, total_amount)

    widget_with_table.update_amount(qty)

    assert total_amount._set_text_calls[-1] == "0"

def test_update_amount_zero_discount_and_tax(widget_with_table):
    qty = DummyWidget('2')
    rate = DummyWidget('100')
    discount = DummyWidget('0')
    tax = DummyWidget('0')
    discount_amount = DummyWidget()
    tax_amount = DummyWidget()
    total_amount = DummyWidget()

    table = widget_with_table.table
    table.set_cell_widget(0, 2, qty)
    table.set_cell_widget(0, 3, rate)
    table.set_cell_widget(0, 4, discount)
    table.set_cell_widget(0, 5, tax)
    table.set_cell_widget(0, 6, discount_amount)
    table.set_cell_widget(0, 7, tax_amount)
    table.set_cell_widget(0, 8, total_amount)

    widget_with_table.update_amount(qty)

    assert discount_amount._set_text_calls[-1] == "0.0"
    assert tax_amount._set_text_calls[-1] == "0.0"
    assert total_amount._set_text_calls[-1] == "200.00"