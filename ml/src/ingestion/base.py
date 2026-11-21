from abc import ABC, abstractmethod
from typing import Any


class DataSource(ABC):
    """Abstract interface for all NexOrbit data sources."""

    @abstractmethod
    def fetch(self) -> Any:
        """Fetch source data into a cached or in-memory representation."""

    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate source-specific schemas and required values."""

    @abstractmethod
    def load(self, data: Any) -> int:
        """Persist validated data and return the number of records processed."""
