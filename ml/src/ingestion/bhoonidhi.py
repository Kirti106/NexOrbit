"""Deferred Bhoonidhi source.

Not implemented: authentication, API availability, product identifiers,
data formats, and download workflow are unknown.
"""

from typing import Any
from .base import DataSource


class BhoonidhiSource(DataSource):
    def fetch(self) -> Any:
        raise NotImplementedError("TODO: confirm Bhoonidhi authentication and API")

    def validate(self, data: Any) -> bool:
        raise NotImplementedError("TODO: define Bhoonidhi file/product format")

    def load(self, data: Any) -> int:
        raise NotImplementedError("TODO: define Bhoonidhi persistence contract")
