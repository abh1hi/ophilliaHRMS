"""Load seed templates from JSON files into the database."""
import json
import logging
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import OnboardingTemplate

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


async def seed_templates(db: AsyncSession) -> int:
    """Insert seed templates if they don't already exist. Returns count of inserted templates."""
    result = await db.execute(select(func.count()).select_from(OnboardingTemplate))
    existing = result.scalar() or 0
    if existing > 0:
        logger.info(f"Templates already seeded ({existing} found) — skipping")
        return 0

    count = 0
    for json_file in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            template = OnboardingTemplate(
                category=data["category"],
                region=data["region"],
                name=data["name"],
                template_json=json.dumps(data),
            )
            db.add(template)
            count += 1
        except Exception as exc:
            logger.error(f"Failed to load template {json_file.name}: {exc}")

    if count:
        await db.commit()
        logger.info(f"Seeded {count} onboarding templates")

    return count
