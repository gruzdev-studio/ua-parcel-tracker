"""The UA Parcel Tracker integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .carriers import get_carrier_class
from .carriers.base import ParcelRequest
from .const import CONF_API_KEY, CONF_CARRIER, CONF_NAME, CONF_NUMBER, CONF_PARCELS, CONF_PHONE, DOMAIN
from .coordinator import ParcelCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UA Parcel Tracker from a config entry."""
    session = async_get_clientsession(hass)
    carrier_cls = get_carrier_class(entry.data[CONF_CARRIER])
    carrier = carrier_cls(session, entry.data[CONF_API_KEY])

    parcels = [
        ParcelRequest(
            number=item[CONF_NUMBER],
            phone=item.get(CONF_PHONE) or None,
            name=item.get(CONF_NAME) or None,
        )
        for item in entry.options.get(CONF_PARCELS, [])
    ]

    coordinator = ParcelCoordinator(hass, entry, carrier, parcels)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Adding or removing parcels changes options; reload to rebuild the entity list.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
