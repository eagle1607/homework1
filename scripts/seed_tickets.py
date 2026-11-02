"""Seed the ticket table with random sample data. Usage: python -m scripts.seed_tickets [count]"""
import random
import sys
from datetime import datetime, timedelta, timezone

from app.config.config import get_settings
from app.config.database import Base, make_session_factory
from sqlalchemy import select

from app.model.model_db import SEVERITY_LEVEL, Ticket, TicketIntent, TicketSeverity, TicketStatus, User, compute_deadline

SUMMARY_TEMPLATES = [
    "Customer cannot log in to their account",
    "Invoice amount does not match the subscription plan",
    "App crashes when uploading a file",
    "Refund request for duplicate charge",
    "Unable to reset password via email link",
    "Feature request: export data to CSV",
    "Payment failed with error code {code}",
    "Dashboard shows incorrect usage statistics",
    "API returns 500 error on bulk import",
    "Account suspended without explanation",
]
PRODUCTS = [None, "web", "mobile", "api", "billing-portal"]


def random_ticket(user_ids: list[int]) -> Ticket:
    created_at = datetime.now(timezone.utc) - timedelta(days=random.uniform(0, 90))
    updated_at = created_at + timedelta(hours=random.uniform(0, 48))
    summary = random.choice(SUMMARY_TEMPLATES).format(code=random.randint(100, 999))
    severity = random.choice(list(TicketSeverity))
    status = random.choice(list(TicketStatus))
    return Ticket(
        intent=random.choice(list(TicketIntent)),
        severity=severity,
        level=SEVERITY_LEVEL[severity],
        status=status,
        related_user=random.choice(user_ids),
        assigned_user=None if status == TicketStatus.OPEN else random.choice(user_ids),
        product=random.choice(PRODUCTS),
        summary=summary,
        needs_human_review=random.random() < 0.3,
        deadline=compute_deadline(severity, created_at),
        created_at=created_at,
        updated_at=updated_at,
    )


def seed(count: int) -> None:
    settings = get_settings()
    engine, session_factory = make_session_factory(settings.database_uri)
    Base.metadata.create_all(engine)
    with session_factory() as db:
        user_ids = list(db.scalars(select(User.id)))
        if not user_ids:
            sys.exit("No users found. Register at least one user before seeding tickets.")
        db.add_all(random_ticket(user_ids) for _ in range(count))
        db.commit()
    print(f"Inserted {count} sample tickets into {engine.url.render_as_string(hide_password=True)}")


if __name__ == "__main__":
    seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
