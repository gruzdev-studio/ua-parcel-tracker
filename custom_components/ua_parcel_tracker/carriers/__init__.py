"""Registry of supported parcel carriers."""

from __future__ import annotations

from .base import Carrier
from .nova_poshta import NovaPoshtaCarrier

CARRIERS: dict[str, type[Carrier]] = {
    NovaPoshtaCarrier.key: NovaPoshtaCarrier,
}


def get_carrier_class(key: str) -> type[Carrier]:
    """Return the carrier class for a given key."""
    return CARRIERS[key]
