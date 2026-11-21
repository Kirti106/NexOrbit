"""Deferred Bhuvan source.

Not implemented: exact OGC endpoints, layer names, authentication requirements,
coordinate conventions, and available WMS/WFS capabilities are unknown.
"""

from typing import Any
from .base import DataSource


class BhuvanSource(DataSource):
    def fetch(self) -> Any:
        raise NotImplementedError("TODO: confirm Bhuvan OGC services and layer names")

    def validate(self, data: Any) -> bool:
        raise NotImplementedError("TODO: define Bhuvan WMS/WFS schema")

    def load(self, data: Any) -> int:
        raise NotImplementedError("TODO: define Bhuvan persistence contract")
