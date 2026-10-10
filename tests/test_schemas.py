import pytest
from pydantic import ValidationError
from app.schemas.request import OrderDetails


def test_valid_order_details():
    order = OrderDetails(
        amount=150.50, currency="USD", item_category="Electronics"
    )
    assert order.amount == 150.50
    assert order.currency == "USD"


def test_invalid_order_amount():
    with pytest.raises(ValidationError):
        OrderDetails(amount=-10.0, currency="USD", item_category="Electronics")