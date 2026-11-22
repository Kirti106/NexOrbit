from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

REQUIRED_TABLES = ("satellites", "gp_history", "conjunctions")


def database_is_available(db: Session) -> bool:
    db.execute(text("SELECT 1"))
    return True


def required_tables_available(db: Session) -> dict[str, bool]:
    existing = set(inspect(db.get_bind()).get_table_names())
    return {table: table in existing for table in REQUIRED_TABLES}
