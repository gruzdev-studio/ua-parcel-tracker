"""Base types shared by all parcel carriers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ParcelStatus(StrEnum):
    """Normalized status shared by all carriers.

    Automations depend on these values, so carriers must map their own
    statuses onto this set and never expose raw carrier codes as state.
    """

    UNKNOWN = "unknown"
    NOT_FOUND = "not_found"
    CREATED = "created"
    IN_TRANSIT = "in_transit"
    READY_FOR_PICKUP = "ready_for_pickup"
    DELIVERED = "delivered"
    RETURNED = "returned"


class CarrierError(Exception):
    """Raised when a carrier API request fails."""


@dataclass(frozen=True)
class ParcelRequest:
    """A parcel the user wants to track."""

    number: str
    phone: str | None = None
    name: str | None = None


@dataclass
class ParcelInfo:
    """Current state of a parcel as returned by a carrier."""

    number: str
    carrier: str
    status: ParcelStatus
    status_text: str
    last_update: datetime | None = None
    location: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class Carrier(ABC):
    """Interface every carrier implements."""

    key: str
    name: str

    def __init__(self, session: Any, api_key: str | None = None) -> None:
        self._session = session
        self._api_key = api_key

    @abstractmethod
    async def track(self, parcels: list[ParcelRequest]) -> dict[str, ParcelInfo]:
        """Return current info keyed by parcel number.

        Parcels the carrier does not know about are omitted from the result.
        Raises CarrierError on network or API failures.
        """
