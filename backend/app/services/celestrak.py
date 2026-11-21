import requests
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Satellite

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php"


def fetch_tle_group(group: str = "stations") -> list[tuple[str, str, str]]:
    response = requests.get(
        CELESTRAK_URL,
        params={"GROUP": group, "FORMAT": "tle"},
        timeout=30,
        headers={"User-Agent": "NexOrbit/1.0 educational project"},
    )
    response.raise_for_status()

    lines = [line.strip() for line in response.text.splitlines() if line.strip()]
    records = []
    index = 0

    while index + 2 < len(lines):
        name, line1, line2 = lines[index:index + 3]
        if line1.startswith("1 ") and line2.startswith("2 "):
            records.append((name, line1, line2))
            index += 3
        else:
            index += 1

    return records


def sync_tle_group(db: Session, group: str = "stations") -> tuple[int, int]:
    records = fetch_tle_group(group)
    changed = 0

    for name, line1, line2 in records:
        try:
            norad_id = int(line1[2:7].strip())
        except (ValueError, IndexError):
            continue

        epoch = line1[18:32].strip() if len(line1) >= 32 else None
        satellite = db.scalar(
            select(Satellite).where(Satellite.norad_id == norad_id)
        )

        if satellite is None:
            satellite = Satellite(
                norad_id=norad_id,
                name=name,
                line1=line1,
                line2=line2,
                epoch=epoch,
                object_type="unknown",
                source="CelesTrak",
            )
            db.add(satellite)
        else:
            satellite.name = name
            satellite.line1 = line1
            satellite.line2 = line2
            satellite.epoch = epoch
            satellite.source = "CelesTrak"
        changed += 1

    db.commit()
    return len(records), changed
