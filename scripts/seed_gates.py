"""Seed gates A and B. Usage: python -m scripts.seed_gates"""
from sqlalchemy import select

from app.config.config import get_settings
from app.config.database import Base, make_session_factory
from app.model.model_db import Gate, GateStatus

GATE_NAMES = ["A", "B"]


def seed() -> None:
    engine, session_factory = make_session_factory(get_settings().database_uri)
    Base.metadata.create_all(engine)
    with session_factory() as db:
        existing = set(db.scalars(select(Gate.name).where(Gate.name.in_(GATE_NAMES))))
        new = [name for name in GATE_NAMES if name not in existing]
        db.add_all(Gate(name=name, status=GateStatus.AVAILABLE) for name in new)
        db.commit()
    print(f"Inserted gates: {new or 'none (already exist)'}")


if __name__ == "__main__":
    seed()
