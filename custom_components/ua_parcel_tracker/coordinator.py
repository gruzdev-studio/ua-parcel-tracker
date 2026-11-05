"""Coordinator polling a carrier for all configured parcels."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .carriers.base import Carrier, CarrierError, ParcelInfo, ParcelRequest, ParcelStatus
from .const import DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN, EVENT_STATUS_CHANGED

_LOGGER = logging.getLogger(__name__)


class ParcelCoordinator(DataUpdateCoordinator[dict[str, ParcelInfo]]):
    """Fetch statuses for all parcels in a single carrier request."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        carrier: Carrier,
        parcels: list[ParcelRequest],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        self.carrier = carrier
        self.parcels = parcels
        self._last_status: dict[str, ParcelStatus] = {}

    async def _async_update_data(self) -> dict[str, ParcelInfo]:
        if not self.parcels:
            return {}

        try:
            found = await self.carrier.track(self.parcels)
        except CarrierError as err:
            raise UpdateFailed(str(err)) from err

        result: dict[str, ParcelInfo] = {}
        for parcel in self.parcels:
            info = found.get(parcel.number) or ParcelInfo(
                number=parcel.number,
                carrier=self.carrier.key,
                status=ParcelStatus.NOT_FOUND,
                status_text="Не знайдено",
            )
            result[parcel.number] = info
            self._fire_if_changed(info)

        return result

    def _fire_if_changed(self, info: ParcelInfo) -> None:
        """Fire an event when a parcel changes status.

        The first refresh after startup only records the status, so restarting
        Home Assistant does not produce a burst of events.
        """
        previous = self._last_status.get(info.number)
        self._last_status[info.number] = info.status

        if previous is None or previous == info.status:
            return

        self.hass.bus.async_fire(
            EVENT_STATUS_CHANGED,
            {
                "number": info.number,
                "carrier": info.carrier,
                "old_status": previous.value,
                "new_status": info.status.value,
                "status_text": info.status_text,
                "location": info.location,
            },
        )
