try:
    from ml.src.ingestion.celestrak_gp import utc_datetime, CelestrakGpSource
    from ml.src.ingestion.satcat import parse_optional_date, SatcatSource
    from ml.src.ingestion.socrates import parse_utc, SocratesSource
except ModuleNotFoundError:
    from src.ingestion.celestrak_gp import utc_datetime, CelestrakGpSource
    from src.ingestion.satcat import parse_optional_date, SatcatSource
    from src.ingestion.socrates import parse_utc, SocratesSource
from pathlib import Path


def test_timezone_aware_parsing():
    assert utc_datetime("2026-01-01T00:00:00Z").tzinfo is not None
    assert parse_optional_date("2020-01-01").tzinfo is not None
    assert parse_utc("2026-01-01 12:00:00").tzinfo is not None
    assert parse_utc("2026-11-24 21:13:59.569").tzinfo is not None


def test_real_gp_sample_schema():
    path = Path("/app/data/samples/celestrak_gp_active.json")
    if not path.exists():
        path = Path("ml/data/samples/celestrak_gp_active.json")
    source = CelestrakGpSource.from_file(path)
    data = source.fetch()
    assert len(data) == 16929
    assert source.validate(data)
    assert data[0]["MEAN_MOTION_DDOT"] == 0
    assert "ELEMENT_SET_NO" in data[0]


def test_real_satcat_json_schema():
    path = Path("/app/data/samples/celestrak_satcat_active.json")
    if not path.exists():
        path = Path("ml/data/samples/celestrak_satcat_active.json")
    source = SatcatSource(path)
    data = source.fetch()
    assert len(data) == 17498
    assert source.validate(data)
    assert "RCS" in data[0]


def test_real_socrates_schema_and_timezone():
    path = Path("/app/data/samples/socrates_sample.csv")
    if not path.exists():
        path = Path("ml/data/samples/socrates_sample.csv")
    source = SocratesSource(path)
    data = source.fetch()
    assert len(data) == 189379
    assert source.validate(data)
    assert parse_utc(data[0]["TCA"]).tzinfo is not None
