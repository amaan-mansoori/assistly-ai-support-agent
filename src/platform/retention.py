"""Preview or explicitly apply conversation retention cleanup."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.db.database import make_engine, make_session_factory
from src.db.models import Conversation
from src.platform.config import PlatformSettings


def purge_conversations(
    session: Session,
    *,
    older_than: datetime,
    apply: bool = False,
) -> int:
    statement = select(func.count()).select_from(Conversation).where(
        Conversation.created_at < older_than
    )
    count = int(session.scalar(statement) or 0)
    if apply and count:
        session.execute(
            delete(Conversation)
            .where(Conversation.created_at < older_than)
            .execution_options(synchronize_session="fetch")
        )
        session.commit()
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, required=True, help="Retention age in days.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete matching conversations. Without this flag, only preview the count.",
    )
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be a positive integer")
    cutoff = datetime.now(UTC) - timedelta(days=args.days)
    engine = make_engine(PlatformSettings.from_env().database_url)
    try:
        with make_session_factory(engine)() as session:
            deleted_or_matching = purge_conversations(
                session, older_than=cutoff, apply=args.apply
            )
    finally:
        engine.dispose()
    print(json.dumps({
        "cutoff": cutoff.isoformat(),
        "matching_conversations": deleted_or_matching,
        "applied": args.apply,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
