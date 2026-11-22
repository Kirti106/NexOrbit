"""Load the checked-in sample datasets into an empty NexOrbit database."""

from pathlib import Path

from sqlalchemy import text

from .pipeline import load_from_file
from .utils.storage import create_database_engine

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"
GP_FILES = (
    "celestrak_gp_active.json",
    "celestrak_gp_cosmos-1408-debris.json",
    "celestrak_gp_cosmos-2251-debris.json",
    "celestrak_gp_fengyun-1c-debris.json",
    "celestrak_gp_iridium-33-debris.json",
)


def _is_empty(table: str) -> bool:
    with create_database_engine().connect() as connection:
        return connection.execute(text(f"SELECT EXISTS (SELECT 1 FROM {table})")).scalar_one() is False


def seed_samples() -> dict[str, int]:
    loaded: dict[str, int] = {}
    if _is_empty("satellites"):
        loaded["satcat"] = load_from_file(
            "satcat", SAMPLES / "celestrak_satcat_active.json"
        )
    if _is_empty("gp_history"):
        loaded["gp_history"] = sum(
            load_from_file("gp", SAMPLES / filename) for filename in GP_FILES
        )
    if _is_empty("conjunctions"):
        loaded["conjunctions"] = load_from_file(
            "socrates", SAMPLES / "socrates_sample.csv"
        )
    return loaded


if __name__ == "__main__":
    print(seed_samples())
