"""Config and options flows for UA Parcel Tracker."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_API_KEY,
    CONF_CARRIER,
    CONF_NAME,
    CONF_NUMBER,
    CONF_NUMBERS,
    CONF_PARCELS,
    CONF_PHONE,
    DEFAULT_CARRIER,
    DOMAIN,
    NAME,
)

# Номер ТТН Нової пошти складається з 14 цифр.
NOVA_POSHTA_NUMBER_RE = re.compile(r"^\d{14}$")


class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup: API key."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Ask for the Nova Poshta API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            if not api_key:
                errors[CONF_API_KEY] = "invalid_api_key"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=NAME,
                    data={CONF_API_KEY: api_key, CONF_CARRIER: DEFAULT_CARRIER},
                    options={CONF_PARCELS: []},
                )

        schema = vol.Schema({vol.Required(CONF_API_KEY): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> ParcelTrackerOptionsFlow:
        """Return the options flow handler."""
        return ParcelTrackerOptionsFlow()


class ParcelTrackerOptionsFlow(config_entries.OptionsFlow):
    """Add and remove tracked parcels."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Show the menu."""
        return self.async_show_menu(step_id="init", menu_options=["add_parcel", "remove_parcel"])

    async def async_step_add_parcel(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Add a parcel by its tracking number."""
        errors: dict[str, str] = {}
        parcels = list(self.config_entry.options.get(CONF_PARCELS, []))

        if user_input is not None:
            number = user_input[CONF_NUMBER].strip()
            if not NOVA_POSHTA_NUMBER_RE.match(number):
                errors[CONF_NUMBER] = "invalid_number"
            elif any(item[CONF_NUMBER] == number for item in parcels):
                errors[CONF_NUMBER] = "already_exists"
            else:
                parcels.append(
                    {
                        CONF_NUMBER: number,
                        CONF_PHONE: (user_input.get(CONF_PHONE) or "").strip(),
                        CONF_NAME: (user_input.get(CONF_NAME) or "").strip(),
                    }
                )
                return self._save_parcels(parcels)

        schema = vol.Schema(
            {
                vol.Required(CONF_NUMBER): str,
                vol.Optional(CONF_PHONE, default=""): str,
                vol.Optional(CONF_NAME, default=""): str,
            }
        )
        return self.async_show_form(step_id="add_parcel", data_schema=schema, errors=errors)

    async def async_step_remove_parcel(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Remove one or more parcels."""
        parcels = list(self.config_entry.options.get(CONF_PARCELS, []))
        if not parcels:
            return self.async_abort(reason="no_parcels")

        if user_input is not None:
            to_remove = set(user_input[CONF_NUMBERS])
            return self._save_parcels(
                [item for item in parcels if item[CONF_NUMBER] not in to_remove]
            )

        choices = {item[CONF_NUMBER]: item[CONF_NAME] or item[CONF_NUMBER] for item in parcels}
        schema = vol.Schema({vol.Required(CONF_NUMBERS): cv.multi_select(choices)})
        return self.async_show_form(step_id="remove_parcel", data_schema=schema)

    def _save_parcels(self, parcels: list[dict[str, str]]) -> FlowResult:
        """Store the new parcel list; the update listener reloads the entry."""
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, CONF_PARCELS: parcels},
        )
        return self.async_create_entry(title="", data={})
