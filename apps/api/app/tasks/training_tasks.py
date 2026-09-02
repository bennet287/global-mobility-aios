from __future__ import annotations

from celery import shared_task
from sqlmodel import Session

from app.core.db import engine
from app.services.training_case_generator import generate_training_cases


@shared_task(bind=True, max_retries=2)
def generate_training_cases_task(self, count: int = 5, country: str | None = None, profession: str | None = None) -> list[str]:
    try:
        with Session(engine) as session:
            cases = generate_training_cases(session, count=count, country=country, profession=profession)
            return [str(case.id) for case in cases]
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
