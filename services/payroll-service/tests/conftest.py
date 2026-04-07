"""Pytest Configuration & Shared Fixtures for Payroll Service Tests.

Provides:
- Database fixtures (async SQLAlchemy)
- Mock objects (employees, salary structures, payroll runs)
- Common test data (test company, test employees, test periods)
- Factories for creating test objects
"""
import pytest
import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.payroll import (
    Base, SalaryStructure, EmployeeSalary, PayrollRun, Payslip,
    EmployeeTaxProfile, EmployeeYTD, PayrollAdjustment, PayrollLoan,
)
from app.core.constants import PayrollStatus, TaxRegime


# ──────────────────────────────────────────────────────────────────────────
# Database Fixtures
# ──────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for each test."""
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ──────────────────────────────────────────────────────────────────────────
# Test Data Constants
# ──────────────────────────────────────────────────────────────────────────

COMPANY_ID = uuid4()
COMPANY_ID_STR = str(COMPANY_ID)

TEST_EMPLOYEES = [
    {
        "id": uuid4(),
        "name": "Ramesh Kumar",
        "designation": "Senior Engineer",
        "department": "Engineering",
        "joining_date": date(2020, 1, 15),
        "ctc": Decimal("1200000"),  # ₹12,00,000
    },
    {
        "id": uuid4(),
        "name": "Priya Sharma",
        "designation": "Product Manager",
        "department": "Product",
        "joining_date": date(2019, 6, 1),
        "ctc": Decimal("1500000"),  # ₹15,00,000
    },
    {
        "id": uuid4(),
        "name": "Arun Verma",
        "designation": "DevOps Engineer",
        "department": "Infrastructure",
        "joining_date": date(2021, 3, 10),
        "ctc": Decimal("800000"),  # ₹8,00,000
    },
]

TEST_SALARY_STRUCTURE = {
    "name": "Standard Engineer",
    "basic_pct": Decimal("50.0"),
    "hra_pct": Decimal("20.0"),
    "allowances_pct": Decimal("30.0"),
    "pf_pct": Decimal("12.0"),
    "esi_pct": Decimal("1.75"),
    "professional_tax": Decimal("200.0"),
}

APRIL_2026_PERIOD = {
    "start": date(2026, 4, 1),
    "end": date(2026, 4, 30),
}


# ──────────────────────────────────────────────────────────────────────────
# Factory Fixtures
# ──────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def company(db_session):
    """Create test company."""
    # In real system, would come from company service
    # For now, we use company_id as context
    return {"id": COMPANY_ID, "name": "OphilliaHRMS Test"}


@pytest.fixture
async def salary_structure(db_session):
    """Create test salary structure."""
    structure = SalaryStructure(
        company_id=COMPANY_ID,
        **TEST_SALARY_STRUCTURE,
    )
    db_session.add(structure)
    await db_session.commit()
    await db_session.refresh(structure)
    return structure


@pytest.fixture
async def employee_salaries(db_session, salary_structure):
    """Create test employee salaries."""
    salaries = []
    for emp in TEST_EMPLOYEES:
        salary = EmployeeSalary(
            company_id=COMPANY_ID,
            employee_id=emp["id"],
            salary_structure_id=salary_structure.id,
            ctc=emp["ctc"],
            effective_from=emp["joining_date"],
            effective_to=None,
        )
        db_session.add(salary)
        salaries.append(salary)

    await db_session.commit()
    for salary in salaries:
        await db_session.refresh(salary)
    return salaries


@pytest.fixture
async def payroll_run(db_session):
    """Create test payroll run in DRAFT state."""
    run = PayrollRun(
        company_id=COMPANY_ID,
        period_start=APRIL_2026_PERIOD["start"],
        period_end=APRIL_2026_PERIOD["end"],
        status=PayrollStatus.DRAFT.value,
        run_type="REGULAR",
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)
    return run


@pytest.fixture
async def employee_tax_profile(db_session):
    """Create test employee tax profile."""
    emp_id = TEST_EMPLOYEES[0]["id"]
    profile = EmployeeTaxProfile(
        company_id=COMPANY_ID,
        employee_id=emp_id,
        financial_year=2026,
        tax_regime="new",
        investment_80c=Decimal("150000"),
        investment_80d=Decimal("25000"),
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest.fixture
async def employee_ytd(db_session):
    """Create test employee YTD record."""
    emp_id = TEST_EMPLOYEES[0]["id"]
    ytd = EmployeeYTD(
        company_id=COMPANY_ID,
        employee_id=emp_id,
        financial_year=2026,
        ytd_gross=Decimal("0"),
        ytd_basic=Decimal("0"),
        ytd_tds=Decimal("0"),
    )
    db_session.add(ytd)
    await db_session.commit()
    await db_session.refresh(ytd)
    return ytd


@pytest.fixture
async def payroll_adjustment(db_session, payroll_run, employee_salaries):
    """Create test payroll adjustment (bonus)."""
    adjustment = PayrollAdjustment(
        company_id=COMPANY_ID,
        payroll_run_id=payroll_run.id,
        employee_id=employee_salaries[0].employee_id,
        adjustment_type="BONUS",
        amount=Decimal("10000"),
        direction="CREDIT",
        taxable=True,
    )
    db_session.add(adjustment)
    await db_session.commit()
    await db_session.refresh(adjustment)
    return adjustment


@pytest.fixture
async def payroll_loan(db_session):
    """Create test payroll loan."""
    emp_id = TEST_EMPLOYEES[0]["id"]
    loan = PayrollLoan(
        company_id=COMPANY_ID,
        employee_id=emp_id,
        loan_type="ADVANCE",
        principal=Decimal("50000"),
        outstanding=Decimal("45000"),
        emi_amount=Decimal("5000"),
        start_month="2026-04",
        end_month="2026-09",
        status="ACTIVE",
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)
    return loan


# ──────────────────────────────────────────────────────────────────────────
# Marker Definitions
# ──────────────────────────────────────────────────────────────────────────

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for single functions")
    config.addinivalue_line("markers", "integration: Integration tests for workflows")
    config.addinivalue_line("markers", "compliance: Compliance tests for India-specific rules")
    config.addinivalue_line("markers", "guard: Tests for Phase 9A guards")
    config.addinivalue_line("markers", "slow: Slow running tests")
