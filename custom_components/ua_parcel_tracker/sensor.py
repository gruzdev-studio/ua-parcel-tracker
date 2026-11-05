"""Sensor platform: one sensor per tracked parcel."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .carriers.base import ParcelInfo, ParcelRequest, ParcelStatus
from .const import DOMAIN
from .coordinator import ParcelCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a sensor for each parcel in the entry options."""
    coordinator: ParcelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(ParcelSensor(coordinator, parcel) for parcel in coordinator.parcels)


class ParcelSensor(CoordinatorEntity[ParcelCoordinator], SensorEntity):
    """Current normalized status of one parcel."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [status.value for status in ParcelStatus]
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, coordinator: ParcelCoordinator, parcel: ParcelRequest) -> None:
        super().__init__(coordinator)
        self._number = parcel.number
        self._attr_name = parcel.name or f"Посилка {parcel.number}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{parcel.number}"

    @property
    def _info(self) -> ParcelInfo | None:
        return (self.coordinator.data or {}).get(self._number)

    @property
    def native_value(self) -> str:
        info = self._info
        return info.status.value if info else ParcelStatus.UNKNOWN.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = self._info
        if info is None:
            return {"number": self._number}
        return {
            "number": info.number,
            "carrier": info.carrier,
            "status_text": info.status_text,
            "location": info.location,
            "last_update": info.last_update.isoformat() if info.last_update else None,
            "history": info.history,
        }
