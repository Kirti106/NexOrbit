"""Top-level orchestration helpers for NexOrbit ML tasks."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import json
import yaml

from .ingestion.celestrak_gp import CelestrakGpSource
from .ingestion.satcat import SatcatSource
from .ingestion.socrates import SocratesSource


def load_yaml(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as source:
        return yaml.safe_load(source) or {}


def sync_gp_group(
    group: str,
    *,
    sources_path: str | Path = "ml/configs/sources.yaml",
) -> int:
    sources = load_yaml(sources_path)
    config = sources["celestrak_gp"]
    source = CelestrakGpSource(
        base_url=config["base_url"],
        group=group,
        timeout_seconds=config["timeout_seconds"],
        retry_attempts=config["retry_attempts"],
        retry_backoff_seconds=config["retry_backoff_seconds"],
        cache_ttl_seconds=config["cache_ttl_seconds"],
        user_agent=config["user_agent"],
        cache_dir="ml/data/raw",
    )
    data = source.fetch()
    source.validate(data)
    return source.load(data)


def load_from_file(source: str, path: str | Path) -> int:
    path = Path(path)
    if source == "gp":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        ingestion = CelestrakGpSource.from_file(path)
    elif source == "satcat":
        ingestion = SatcatSource(path)
        data = ingestion.fetch()
    elif source == "socrates":
        ingestion = SocratesSource(path)
        data = ingestion.fetch()
    else:
        raise ValueError("source must be gp, satcat, or socrates")
    ingestion.validate(data)
    return ingestion.load(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="NexOrbit ML ingestion")
    parser.add_argument("--source", choices=["gp", "satcat", "socrates"])
    parser.add_argument("--from-file", dest="from_file")
    parser.add_argument("--group", default="active")
    parser.add_argument("--conjunctions-refresh", action="store_true")
    parser.add_argument("--anomalies-recompute", action="store_true")
    args = parser.parse_args()

    if args.conjunctions_refresh:
        if not args.from_file:
            raise NotImplementedError(
                "Live SOCRATES refresh is not configured; use --from-file "
                "until a verified downloadable CSV endpoint is added."
            )
        print(load_from_file("socrates", args.from_file))
        return
    if args.anomalies_recompute:
        from .api.app import anomalies
        from .utils.storage import insert_model_run, insert_prediction, session_scope

        result = anomalies(limit=500)
        with session_scope() as session:
            model_run_id = insert_model_run(
                session,
                task="anomaly",
                model_name="cross-sectional-robust-z",
                version="2026-11-22-v1",
                params={"features": ["mean_motion", "eccentricity", "inclination", "bstar"]},
                metrics={"scope": "cross-sectional one-epoch profile"},
            )
            for item in result.items:
                insert_prediction(
                    session,
                    model_run_id=model_run_id,
                    norad_cat_id=item.norad_id,
                    target_time=result.generated_at,
                    output={
                        "score": item.score,
                        "flag": item.score >= 6.0,
                        "top_contributing_feature": item.top_feature,
                        "label": item.label,
                        "basis": "cross-sectional element profile, not maneuver detection",
                    },
                )
        print(len(result.items))
        return
    if args.from_file:
        if not args.source:
            parser.error("--source is required with --from-file")
        print(load_from_file(args.source, args.from_file))
        return
    if args.source == "gp":
        print(sync_gp_group(args.group))
        return
    parser.error("Use --source gp with --group, or --source and --from-file")


if __name__ == "__main__":
    main()
