from src.models import Apartment, Bill, Parameters, Tenant, Transfer, ApartmentSettlement, TenantSettlement
import calendar
from datetime import date

class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []

        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(
        self,
        apartment_key: str,
        year: int | None = None,
        month: int | None = None,
    ) -> float | None:
        if apartment_key not in self.apartments:
            return None

        if month is not None and not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}. Expected value between 1 and 12.")

        total = 0.0
        for bill in self.bills:
            if bill.apartment != apartment_key:
                continue
            if year is not None and bill.settlement_year != year:
                continue
            if month is not None and bill.settlement_month != month:
                continue
            total += bill.amount_pln

        return round(total, 2)

    def create_apartment_settlement(
        self,
        apartment_key: str,
        year: int,
        month: int,
    ) -> ApartmentSettlement | None:
        total_bills = self.get_apartment_costs(apartment_key, year, month)
        if total_bills is None:
            return None

        total_rent = 0.0  # rozliczenia najemców pominięte w tym kroku
        total_transfers = 0.0  # przelewy zostaną uwzględnione w kolejnym kroku
        total_due = round(total_rent + total_bills, 2)
        balance = round(total_transfers - total_bills, 2)

        return ApartmentSettlement(
            apartment=apartment_key,
            year=year,
            month=month,
            total_rent_pln=total_rent,
            total_bills_pln=total_bills,
            total_due_pln=total_due,
            balance_pln=balance,
        )

    def _is_tenant_active_in_month(self, tenant: Tenant, year: int, month: int) -> bool:
        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        agreement_from = date.fromisoformat(tenant.date_agreement_from)
        agreement_to = date.fromisoformat(tenant.date_agreement_to)
        return agreement_from <= month_end and agreement_to >= month_start

    def create_tenant_settlements(
        self,
        apartment_settlement: ApartmentSettlement,
    ) -> list[TenantSettlement]:
        active_tenants = {
            tenant_key: tenant
            for tenant_key, tenant in self.tenants.items()
            if tenant.apartment == apartment_settlement.apartment
            and self._is_tenant_active_in_month(
                tenant, apartment_settlement.year, apartment_settlement.month
            )
        }

        if not active_tenants:
            return []

        bills_share = round(
            apartment_settlement.total_bills_pln / len(active_tenants), 2
        )
        settlement_id = (
            f"{apartment_settlement.apartment}-"
            f"{apartment_settlement.year}-"
            f"{apartment_settlement.month:02d}"
        )

        settlements: list[TenantSettlement] = []
        for tenant_key, tenant in active_tenants.items():
            total_due = round(tenant.rent_pln + bills_share, 2)
            balance = round(0.0 - total_due, 2)  # przelewy będą uwzględnione później
            settlements.append(
                TenantSettlement(
                    tenant=tenant_key,
                    apartment_settlement=settlement_id,
                    month=apartment_settlement.month,
                    year=apartment_settlement.year,
                    rent_pln=tenant.rent_pln,
                    bills_pln=bills_share,
                    total_due_pln=total_due,
                    balance_pln=balance,
                )
            )

        return settlements