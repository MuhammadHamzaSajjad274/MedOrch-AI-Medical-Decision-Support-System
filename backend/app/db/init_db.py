"""Create database tables. Run once or on startup."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path when run as script
_backend = Path(__file__).resolve().parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


async def main() -> int:
    from app.db.database import init_db
    await init_db()
    print("Database tables created.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
