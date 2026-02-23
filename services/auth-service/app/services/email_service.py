import logging

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    async def send_magic_link(email: str, link: str) -> None:
        # TODO: Integrate with SendGrid / AWS SES in production
        logger.info(f"[EMAIL] Magic link for {email}: {link}")

    @staticmethod
    async def send_password_reset(email: str, link: str) -> None:
        # TODO: Integrate with SendGrid / AWS SES in production
        logger.info(f"[EMAIL] Password reset link for {email}: {link}")
