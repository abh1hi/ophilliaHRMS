"""
Seeder script to create users in the auth service database.

Usage:
    python seed_user.py --email admin@example.com --password Secret123 --role super_admin --company "Ophillia Inc"

Roles: super_admin, hr, manager, employee (default: employee)
"""

import argparse
import asyncio
import sys

from sqlalchemy import select

from app.core.config import settings  # noqa: E402 — loads .env
from app.core.constants import UserRole
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import Company, User


async def seed_user(
    email: str,
    password: str,
    role: str,
    company_name: str,
) -> None:
    async with AsyncSessionLocal() as session:
        # --- resolve or create company ---
        result = await session.execute(
            select(Company).where(Company.name == company_name)
        )
        company = result.scalars().first()

        if company is None:
            company = Company(name=company_name)
            session.add(company)
            await session.flush()
            print(f"Created company: {company_name} (id={company.id})")
        else:
            print(f"Using existing company: {company_name} (id={company.id})")

        # --- check for duplicate email ---
        existing = await session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        if existing.scalars().first():
            print(f"User with email '{email}' already exists. Aborting.")
            sys.exit(1)

        # --- create user ---
        user = User(
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            role=role,
            company_id=company.id,
        )
        session.add(user)
        await session.commit()

        print(f"User created successfully:")
        print(f"  ID:      {user.id}")
        print(f"  Email:   {user.email}")
        print(f"  Role:    {user.role}")
        print(f"  Company: {company_name}")


def main() -> None:
    valid_roles = [r.value for r in UserRole]

    parser = argparse.ArgumentParser(description="Seed a user into the auth database")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--password", required=True, help="Plain-text password")
    parser.add_argument(
        "--role",
        default=UserRole.EMPLOYEE.value,
        choices=valid_roles,
        help=f"User role (default: employee). Choices: {', '.join(valid_roles)}",
    )
    parser.add_argument(
        "--company",
        default="Default Company",
        help='Company name (created if it does not exist, default: "Default Company")',
    )

    args = parser.parse_args()

    asyncio.run(seed_user(args.email, args.password, args.role, args.company))


if __name__ == "__main__":
    main()
