from src.manager import Manager
from src.models import Parameters, Tenant, TenantSettlement


def test_create_tenant_settlements():
    manager = Manager(Parameters())
    apartment_settlement = manager.create_apartment_settlement("apart-polanka", 2025, 1)
    assert apartment_settlement is not None
    assert apartment_settlement.total_bills_pln == 910.0

    # 1. Mieszkanie z 2 aktywnymi najemcami (+ 1 z wygasłą umową i 1 z innego mieszkania)
    # Równy podział rachunków: 910.0 / 2 = 455.0 na osobę
    manager.tenants = {
        "tenant-1": Tenant(
            name="Jan Nowak",
            apartment="apart-polanka",
            room="room-1",
            rent_pln=1000.0,
            deposit_pln=1000.0,
            date_agreement_from="2024-10-01",
            date_agreement_to="2025-09-30",
        ),
        "tenant-2": Tenant(
            name="Adam Kowalski",
            apartment="apart-polanka",
            room="room-2",
            rent_pln=1200.0,
            deposit_pln=1200.0,
            date_agreement_from="2024-10-01",
            date_agreement_to="2025-09-30",
        ),
        "tenant-expired": Tenant(
            name="Były Najemca",
            apartment="apart-polanka",
            room="room-3",
            rent_pln=900.0,
            deposit_pln=900.0,
            date_agreement_from="2024-01-01",
            date_agreement_to="2024-12-31",
        ),
        "tenant-other": Tenant(
            name="Ewa Adamska",
            apartment="other-apart",
            room="room-1",
            rent_pln=1100.0,
            deposit_pln=1100.0,
            date_agreement_from="2024-10-01",
            date_agreement_to="2025-09-30",
        ),
    }

    settlements = manager.create_tenant_settlements(apartment_settlement)
    settlements_by_tenant = {s.tenant: s for s in settlements}

    assert len(settlements) == 2
    assert all(isinstance(s, TenantSettlement) for s in settlements)
    assert "tenant-expired" not in settlements_by_tenant
    assert "tenant-other" not in settlements_by_tenant

    t1 = settlements_by_tenant["tenant-1"]
    assert t1.apartment_settlement == "apart-polanka-2025-01"
    assert t1.year == 2025
    assert t1.month == 1
    assert t1.rent_pln == 1000.0
    assert t1.bills_pln == 455.0
    assert t1.total_due_pln == 1455.0
    assert t1.balance_pln == -1455.0

    t2 = settlements_by_tenant["tenant-2"]
    assert t2.bills_pln == 455.0
    assert t2.total_due_pln == 1655.0
    assert t2.balance_pln == -1655.0

    # 2. Mieszkanie z tylko 1 aktywnym najemcą -> cały koszt rachunków (910.0)
    manager.tenants = {"tenant-1": manager.tenants["tenant-1"]}
    single_settlements = manager.create_tenant_settlements(apartment_settlement)

    assert len(single_settlements) == 1
    assert single_settlements[0].tenant == "tenant-1"
    assert single_settlements[0].bills_pln == 910.0
    assert single_settlements[0].total_due_pln == 1910.0
    assert single_settlements[0].balance_pln == -1910.0

    # 3. Mieszkanie bez żadnych najemców -> brak rozliczeń
    manager.tenants = {}
    empty_settlements = manager.create_tenant_settlements(apartment_settlement)

    assert empty_settlements == []