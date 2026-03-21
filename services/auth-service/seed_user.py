"""
Seeder script — the ONLY way to create the first super_admin.

Run inside the auth-service container:
    docker exec hrms-auth python seed_user.py \
        --email admin@example.com \
        --password 'S3cure!Pass9' \
        --role super_admin \
        --company "Ophillia Inc"

Roles: super_admin, hr, manager, employee (default: employee)

SECURITY NOTE:
  This script requires shell access to the container, which means
  only operators with server/container access can bootstrap the first
  super_admin. All subsequent user creation should go through the
  authenticated POST /api/v1/auth/users endpoint.
"""

import argparse
import asyncio
import re
import sys

from sqlalchemy import select

from app.core.config import settings  # noqa: E402 — loads .env
from app.core.constants import UserRole
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import Company, User
from app.models.token import RefreshToken  # noqa: F401 — needed for SQLAlchemy relationship resolution
from app.models.magic_token import MagicToken  # noqa: F401


def validate_password(password: str) -> None:
    """Enforce the same rules as the API schema."""
    errors = []
    if len(password) < 10:
        errors.append("at least 10 characters")
    if len(password) > 100:
        errors.append("at most 100 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("one digit")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/\\`~]", password):
        errors.append("one special character")
    if errors:
        print(f"Password too weak — must contain: {', '.join(errors)}")
        sys.exit(1)


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

    parser = argparse.ArgumentParser(
        description="Seed a user into the auth database",
        epilog=(
            "TIP: Use --prompt-password to enter the password interactively.\n"
            "This avoids shell-expansion issues with special characters like ! $ `\n\n"
            "Example:\n"
            "  docker exec -it hrms-auth python seed_user.py \\\n"
            "    --email admin@example.com --prompt-password \\\n"
            "    --role super_admin --company 'My Corp'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--password", default=None, help="Plain-text password (min 10 chars, upper+lower+digit+special)")
    parser.add_argument(
        "--prompt-password",
        action="store_true",
        help="Prompt for password interactively (avoids shell-escaping issues)",
    )
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

    if args.prompt_password:
        import getpass
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Aborting.")
            sys.exit(1)
    elif args.password:
        password = args.password
    else:
        print("Error: provide --password or --prompt-password")
        sys.exit(1)

    validate_password(password)

    asyncio.run(seed_user(args.email, password, args.role, args.company))


if __name__ == "__main__":
    main()
