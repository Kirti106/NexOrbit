"""Deferred VEDAS source.

Not implemented: authentication, API availability, product formats,
catalog endpoints, and licensing constraints are unknown.
"""

from typing import Any
from .base import DataSource


class VedasSource(DataSource):
    def fetch(self) -> Any:
        raise NotImplementedError("TODO: confirm VEDAS access and API availability")

    def validate(self, data: Any) -> bool:
        raise NotImplementedError("TODO: define VEDAS product formats")

    def load(self, data: Any) -> int:
        raise NotImplementedError("TODO: define VEDAS persistence contract")
