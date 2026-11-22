from src.manager import Manager
from src.models import Bill, Parameters


def test_get_apartment_costs():
    parameters = Parameters()
    manager = Manager(parameters)

    # Mieszkanie ma rachunki w tym miesiącu (760.00 + 150.00 = 910.0)
    assert manager.get_apartment_costs("apart-polanka", 2025, 1) == 910.0

    # Rok się zgadza (2025), ale w tym miesiącu (2) brak rachunków -> 0.0
    assert manager.get_apartment_costs("apart-polanka", 2025, 2) == 0.0

    # Miesiąc się zgadza (1), ale inny rok (2024) -> 0.0
    assert manager.get_apartment_costs("apart-polanka", 2024, 1) == 0.0

    # Mieszkanie nie istnieje w słowniku apartments -> None
    assert manager.get_apartment_costs("invalid-apartment", 2025, 1) is None


def test_get_apartment_costs_ignores_other_months_and_invalid_apartments():
    parameters = Parameters()
    manager = Manager(parameters)

    manager.bills.extend([
        Bill(
            amount_pln=200.0,
            date_due="2025-03-15",
            settlement_year=2025,
            settlement_month=2,
            apartment="apart-polanka",
            type="internet",
        ),
        Bill(
            amount_pln=500.0,
            date_due="2025-02-20",
            settlement_year=2025,
            settlement_month=1,
            apartment="non-existent-key",
            type="rent",
        ),
    ])

    # Rachunek z lutego nie wpływa na sumę za styczeń
    assert manager.get_apartment_costs("apart-polanka", 2025, 1) == 910.0
    # Suma dla lutego uwzględnia tylko nowo dodany rachunek
    assert manager.get_apartment_costs("apart-polanka", 2025, 2) == 200.0
    # Mimo obecności rachunku w bills, brak klucza w apartments zwraca None
    assert manager.get_apartment_costs("non-existent-key", 2025, 1) is None